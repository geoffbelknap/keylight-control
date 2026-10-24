"""Exercise recovery against a local mock light; never contact real devices."""
import asyncio
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from aiohttp import ClientSession, web
from PySide6.QtWidgets import QApplication
from zeroconf import ServiceStateChange

from core.discovery import KeyLightDiscovery
from core.api_http import HttpTransport
from core.api_unix import UnixSocketTransport
from ui.main_window import KeyLightController

app = QApplication.instance() or QApplication([])


class RecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = {"on": 0, "brightness": 20, "temperature": 270}
        self.requests = []
        self.fail_get = self.fail_put = False
        self.hold_put = self.hold_get = False
        self.delay_get = 0
        self.invalid_get = False
        self.put_started, self.put_release = asyncio.Event(), asyncio.Event()
        self.get_started, self.get_release = asyncio.Event(), asyncio.Event()
        server = web.Application()
        server.router.add_route("*", "/elgato/lights", self.endpoint)
        self.runner = web.AppRunner(server)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        self.port = self.site._server.sockets[0].getsockname()[1]

        self.config = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.config.name})
        self.environment.start()
        config_dir = Path(self.config.name) / "keylight-control"
        config_dir.mkdir()
        (config_dir / "device-labels.json").write_text(json.dumps({
            "version": "1.0", "devices": {}, "app_settings": {"advanced.api_enabled": False},
        }))
        self.discovery_patch = patch("ui.main_window.KeyLightDiscovery")
        self.discovery_patch.start()
        self.tray_patch = patch("ui.main_window.create_tray_icon", return_value=Mock())
        self.tray_patch.start()
        self.controller = KeyLightController()
        self.controller.add_keylight({
            "name": "Mock Light", "ip": "127.0.0.1", "port": self.port,
            "mac_address": "MOCKMAC", "service_name": "mock._elg._tcp.local.",
        })
        self.widget = self.controller.keylight_widgets[0]
        await self.widget.refresh_state()
        self.requests.clear()

    async def asyncTearDown(self):
        self.put_release.set()
        self.get_release.set()
        self.controller.quit_application()
        await asyncio.sleep(0)
        self.controller.deleteLater()
        self.tray_patch.stop()
        self.discovery_patch.stop()
        self.environment.stop()
        self.config.cleanup()
        await self.runner.cleanup()

    async def endpoint(self, request):
        payload = await request.json() if request.method == "PUT" else None
        self.requests.append((request.method, payload))
        if request.method == "PUT":
            if self.fail_put:
                raise web.HTTPServiceUnavailable()
            if self.hold_put:
                self.put_started.set()
                await self.put_release.wait()
            self.state.update(payload["lights"][0])
        else:
            if self.delay_get:
                await asyncio.sleep(self.delay_get)
            if self.invalid_get:
                return web.json_response({"lights": []})
            if self.fail_get:
                raise web.HTTPServiceUnavailable()
            if self.hold_get:
                self.get_started.set()
                await self.get_release.wait()
        return web.json_response({"numberOfLights": 1, "lights": [dict(self.state)]})

    def writes(self):
        return [payload["lights"][0] for method, payload in self.requests if method == "PUT"]

    async def test_refresh_updates_controls_without_writes_or_cross_light_sync(self):
        self.controller.all_sync_enabled = True
        self.state.update(on=1, brightness=43, temperature=310)
        await self.widget.refresh_state()
        self.assertTrue(self.widget.keylight.on)
        self.assertEqual(self.widget.brightness_slider.value(), 43)
        self.assertEqual(self.widget.temp_slider.value(), 310)
        self.assertIsNone(self.widget.pending_update)
        self.assertEqual(self.controller.pending_sync_updates, {})
        self.assertEqual(self.writes(), [])

    async def test_poll_interval_is_75_seconds_and_tick_refreshes_state(self):
        self.assertEqual(self.controller.refresh_timer.interval(), 75_000)
        self.state["on"] = 1
        self.controller.refresh_devices()
        await self.widget._refresh_task
        self.assertTrue(self.widget.keylight.on)
        self.assertEqual(self.writes(), [])

    async def test_failed_write_is_visible_and_next_poll_recovers_without_replay(self):
        self.fail_put = True
        self.widget.brightness_slider.setValue(66)
        await self.widget.flush_update()
        self.assertFalse(self.widget.keylight.connected)
        self.assertFalse(self.widget.keylight.state_loaded)
        self.assertIn("Offline", self.widget.connection_label.text())
        self.assertIn("503", self.widget.keylight.last_error)
        self.fail_put = False
        await self.widget.refresh_state()
        self.assertTrue(self.widget.keylight.connected)
        self.assertEqual(self.widget.keylight.brightness, 20)
        self.assertEqual(self.widget.keylight.last_error, "")
        self.assertEqual(len(self.writes()), 1)

    async def test_brightness_change_preserves_external_power_and_temperature(self):
        self.state.update(on=1, temperature=300)
        self.widget.brightness_slider.setValue(55)
        await self.widget.flush_update()
        self.assertEqual(self.state, {"on": 1, "brightness": 55, "temperature": 300})
        self.assertEqual(self.widget.keylight.temperature, 300)
        self.assertTrue(self.widget.keylight.on)

    async def test_newest_slider_value_wins_while_first_write_is_in_flight(self):
        self.hold_put = True
        self.widget.brightness_slider.setValue(66)
        first = asyncio.create_task(self.widget.flush_update())
        await asyncio.wait_for(self.put_started.wait(), 2)
        # Returning to the previously confirmed value is still a new command.
        self.widget.brightness_slider.setValue(20)
        second = asyncio.create_task(self.widget.flush_update())
        await asyncio.sleep(0)
        self.assertEqual(len(self.writes()), 1)
        self.hold_put = False
        self.put_release.set()
        await asyncio.gather(first, second)
        self.assertEqual([state["brightness"] for state in self.writes()], [66, 20])
        self.assertEqual(self.widget.keylight.brightness, 20)
        self.assertFalse(self.widget.keylight.pending)

    async def test_old_poll_does_not_overwrite_new_slider_input(self):
        self.hold_get = True
        self.widget.update_from_device()
        await asyncio.wait_for(self.get_started.wait(), 2)
        self.widget.brightness_slider.setValue(81)
        self.hold_get = False
        self.get_release.set()
        await self.widget._refresh_task
        self.assertEqual(self.widget.keylight.brightness, 81)
        await self.widget.flush_update()
        self.assertEqual(self.state["brightness"], 81)

    async def test_async_toggle_uses_actual_power_and_acknowledges_readback(self):
        self.widget.keylight.on = True  # Deliberately stale cached value.
        result = await self.controller._api.handle_request_async("lights.toggle")
        self.assertTrue(result["ok"], result)
        self.assertEqual(self.state["on"], 1)
        self.assertTrue(result["devices"][0]["ready"])
        self.assertFalse(result["devices"][0]["pending"])

    async def test_async_command_reports_write_failure(self):
        self.fail_put = True
        result = await self.controller._api.handle_request_async("lights.set", {"id": 0, "on": True})
        self.assertFalse(result["ok"], result)
        self.assertIn("503", result["error"])

    async def test_unreachable_light_does_not_receive_a_toggle(self):
        self.fail_get = True
        result = await self.controller._api.handle_request_async("lights.toggle")
        self.assertFalse(result["ok"], result)
        self.assertEqual(self.writes(), [])
        self.fail_get = False
        await self.widget.refresh_state()
        self.assertTrue(self.widget.keylight.connected)

    async def test_address_update_reuses_device_identity_and_refreshes(self):
        second = web.TCPSite(self.runner, "127.0.0.1", 0)
        await second.start()
        port = second._server.sockets[0].getsockname()[1]
        self.controller.add_keylight({"name": "Mock Light", "ip": "127.0.0.1", "port": port,
                                     "mac_address": "MOCKMAC", "service_name": "mock._elg._tcp.local."})
        await self.widget.refresh_state()
        self.assertEqual(len(self.controller.keylights), 1)
        self.assertIs(self.controller.keylight_widgets[0], self.widget)
        self.assertEqual(self.widget.keylight.port, port)
        self.assertTrue(self.widget.keylight.connected)

    async def test_changed_ip_matches_service_even_when_mac_lookup_failed(self):
        with patch.object(self.widget, "endpoint_changed") as reconnect:
            self.controller.add_keylight({"name": "Mock Light", "ip": "192.0.2.55", "port": 9123,
                                         "mac_address": "IP_192_0_2_55", "service_name": "mock._elg._tcp.local."})
            self.assertEqual(len(self.controller.keylights), 1)
            self.assertEqual(self.widget.keylight.ip, "192.0.2.55")
            self.assertEqual(self.widget.keylight.mac_address, "MOCKMAC")
            reconnect.assert_called_once()

    async def test_removed_service_is_marked_offline_but_poll_can_recover(self):
        self.controller.device_removed("mock._elg._tcp.local.")
        self.assertFalse(self.widget.keylight.connected)
        await self.widget.refresh_state()
        self.assertTrue(self.widget.keylight.connected)

    async def test_timeout_is_visible_and_recovers(self):
        self.controller.service._timeout = 0.01
        self.delay_get = 0.05
        await self.widget.refresh_state()
        self.assertFalse(self.widget.keylight.connected)
        self.assertIn("TimeoutError", self.widget.keylight.last_error)
        self.delay_get = 0
        self.controller.service._timeout = 2
        await self.widget.refresh_state()
        self.assertTrue(self.widget.keylight.connected)

    async def test_malformed_state_does_not_become_ready(self):
        self.invalid_get = True
        await self.widget.refresh_state()
        self.assertFalse(self.widget.keylight.state_loaded)
        self.assertFalse(self.widget.keylight.connected)

    async def test_stable_identity_wins_over_another_devices_old_ip(self):
        other = type(self.widget.keylight)("Other", "192.0.2.25", mac_address="OTHER",
                                          service_name="other._elg._tcp.local.")
        self.controller.keylights.append(other)
        self.controller.keylight_widgets.append(Mock(keylight=other))
        self.controller.add_keylight({"name": "Other", "ip": "127.0.0.1", "port": self.port,
                                     "mac_address": "OTHER", "service_name": other.service_name})
        self.assertEqual(self.widget.keylight.mac_address, "MOCKMAC")
        self.assertEqual(other.ip, "127.0.0.1")
        self.assertEqual(len(self.controller.keylights), 2)
        self.controller.keylight_widgets.pop()  # Do not treat the mock as an async widget on teardown.
        self.controller.keylights.pop()

    async def test_concurrent_toggles_are_serialized(self):
        results = await asyncio.gather(*(
            self.controller._api.handle_request_async("lights.toggle") for _ in range(2)))
        self.assertTrue(all(result["ok"] for result in results), results)
        self.assertEqual([state["on"] for state in self.writes()], [1, 0])

    async def test_unix_api_reports_failure_after_the_device_rejects_write(self):
        self.fail_put = True
        path = str(Path(self.config.name) / "control.sock")
        transport = UnixSocketTransport(self.controller._api, path)
        await transport.start()
        try:
            reader, writer = await asyncio.open_unix_connection(path)
            writer.write(b'{"command":"lights.set","params":{"id":0,"on":true}}\n')
            await writer.drain()
            result = json.loads(await asyncio.wait_for(reader.readline(), 3))
            self.assertFalse(result["ok"], result)
            self.assertIn("503", result["error"])
            writer.close()
            await writer.wait_closed()
        finally:
            await transport.stop()

    async def test_http_api_reports_failure_after_the_device_rejects_write(self):
        self.fail_put = True
        transport = HttpTransport(self.controller._api, port=0)
        await transport.start()
        try:
            site = next(iter(transport._runner.sites))
            port = site._server.sockets[0].getsockname()[1]
            async with ClientSession() as client:
                async with client.post(f"http://127.0.0.1:{port}/api/lights/toggle") as response:
                    self.assertEqual(response.status, 400)
                    result = await response.json()
                    self.assertFalse(result["ok"], result)
                    self.assertIn("503", result["error"])
        finally:
            await transport.stop()

    async def test_old_discovery_lookup_cannot_restore_an_outdated_address(self):
        waiting = asyncio.Event()
        async def resolve(ip, port):
            if ip == "192.0.2.1":
                await waiting.wait()
            return "MOCKMAC"
        self.controller.discovery._get_device_mac_address = AsyncMock(side_effect=resolve)
        identity = "changing._elg._tcp.local."
        self.controller.fetch_device_mac({"name": "Changing", "ip": "192.0.2.1", "port": 9123,
                                          "service_name": identity})
        old = self.controller._discovery_tasks[identity]
        await asyncio.sleep(0)
        self.controller.fetch_device_mac({"name": "Changing", "ip": "192.0.2.2", "port": 9123,
                                          "service_name": identity})
        await self.controller._discovery_tasks[identity]
        self.assertTrue(old.cancelled())
        emitted = self.controller.discovery.device_found.emit.call_args.args[0]
        self.assertEqual(emitted["ip"], "192.0.2.2")


class DiscoveryTests(unittest.TestCase):
    def test_updated_and_removed_services_are_not_ignored(self):
        discovery = KeyLightDiscovery()
        changes, removed = [], []
        discovery.mac_fetch_requested.connect(changes.append)
        discovery.device_removed.connect(removed.append)
        zeroconf = Mock()
        zeroconf.get_service_info.return_value = Mock(addresses=[socket.inet_aton("192.0.2.5")], port=9123)
        for state in (ServiceStateChange.Added, ServiceStateChange.Updated, ServiceStateChange.Removed):
            discovery._on_service_state_change(zeroconf, "_elg._tcp.local.", "mock._elg._tcp.local.", state)
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[-1]["ip"], "192.0.2.5")
        self.assertEqual(removed, ["mock._elg._tcp.local."])

    def test_restart_recreates_closed_network_resources(self):
        with patch("core.discovery.Zeroconf") as factory, patch("core.discovery.ServiceBrowser") as browser:
            first, second = Mock(), Mock()
            factory.side_effect = [first, second]
            discovery = KeyLightDiscovery()
            discovery.start_discovery()
            discovery.start_discovery()
            self.assertEqual(factory.call_count, 1)
            discovery.restart_discovery()
            first.close.assert_called_once()
            self.assertEqual(factory.call_count, 2)
            discovery.stop_discovery()
            second.close.assert_called_once()
