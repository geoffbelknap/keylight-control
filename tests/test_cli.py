import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cli
from utils.paths import control_socket_path
from utils.single_instance import SingleInstance


class ClientTests(unittest.TestCase):
    def test_status_never_toggles(self):
        state = {"ok": True, "devices": [{"on": True}]}
        with patch.object(cli, "request", return_value=state) as request:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(cli.main(status=True), 0)
            self.assertEqual(json.loads(output.getvalue()), state)
            request.assert_called_once_with("lights.list")

    def test_status_includes_offline_devices_without_waiting_or_toggling(self):
        state = {"ok": True, "devices": [{"name": "Offline light", "ready": False, "connected": False}]}
        with patch.object(cli, "request", return_value=state) as request:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(cli.main(status=True), 0)
            self.assertEqual(json.loads(output.getvalue()), state)
            request.assert_called_once_with("lights.list")

    def test_cold_start_replaces_client_with_persistent_controller(self):
        for status, action in [(False, "toggle"), (True, "status")]:
            with self.subTest(action=action):
                with patch.object(cli, "request", side_effect=FileNotFoundError()):
                    with patch.object(cli.os, "execv", side_effect=SystemExit(0)) as launch:
                        with self.assertRaises(SystemExit):
                            cli.main(status=status)
                        self.assertEqual(launch.call_args.args[1][-3:],
                                         ["--minimized", "--startup-command", action])
                        self.assertEqual(Path(launch.call_args.args[1][1]).parent, Path(cli.__file__).parent)

    def test_warm_toggle_dispatches_once(self):
        with patch.object(cli, "request", side_effect=[
            {"ok": True, "devices": [{"on": False}]}, {"ok": True}
        ]) as request, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(), 0)
            self.assertEqual([call.args[0] for call in request.call_args_list],
                             ["lights.list", "lights.toggle"])

    def test_timeout_does_not_toggle(self):
        with patch.object(cli, "request", return_value={"ok": True, "devices": []}) as request:
            with patch.object(cli.time, "monotonic", side_effect=[0, 16]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(cli.main(), 1)
            request.assert_called_once_with("lights.list")

    def test_toggle_waits_for_actual_device_state(self):
        with patch.object(cli, "request", side_effect=[
            {"ok": True, "devices": [{"ready": False, "on": False}]},
            {"ok": True, "devices": [{"ready": True, "on": True}]},
            {"ok": True},
        ]) as request, patch.object(cli.time, "sleep"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(), 0)
            self.assertEqual([call.args[0] for call in request.call_args_list],
                             ["lights.list", "lights.list", "lights.toggle"])


class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {
            "XDG_RUNTIME_DIR": self.directory.name,
            "FLATPAK_ID": "io.github.geoffbelknap.keylight-control",
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.directory.cleanup()

    def test_sandbox_socket_is_in_app_runtime(self):
        self.assertEqual(control_socket_path(), str(Path(self.directory.name) / "app" /
            "io.github.geoffbelknap.keylight-control" / "keylight-control.sock"))

    def test_second_instance_activates_first_and_can_restart(self):
        first, second, third = SingleInstance(), SingleInstance(), SingleInstance()
        try:
            self.assertFalse(first.is_running())
            self.assertTrue(second.is_running())
            second.activate_existing()
            connection, _ = first.socket.accept()
            connection.close()
            first.cleanup()
            self.assertFalse(third.is_running())
        finally:
            first.cleanup()
            second.cleanup()
            third.cleanup()


if __name__ == "__main__":
    unittest.main()
