"""Exercise the real Qt entry point with mock lights, without network requests."""
import os
import sys
import tempfile
from unittest.mock import Mock, patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import keylight_controller


action = sys.argv[1]
calls = []
timer_fired = []


class FakeAPI:
    async def handle_request_async(self, command):
        return self.handle_request(command)

    def handle_request(self, command):
        calls.append(command)
        return {"ok": True, "devices": [{"on": False}]}


class FakeController:
    def __init__(self):
        self._api = FakeAPI()
        self.prefs = Mock()
        if action == "toggle":
            # The cold-start toggle must keep serving after dispatching the
            # change; the fake device never touches a physical light.
            def finish():
                timer_fired.append(True)
                self.quit_application()
            QTimer.singleShot(2500, finish)

    def quit_application(self):
        QApplication.instance().quit()


with tempfile.TemporaryDirectory() as runtime:
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": runtime, "FLATPAK_ID": "test"}):
        with patch("ui.main_window.KeyLightController", FakeController):
            with patch.object(sys, "argv", ["keylight-controller", "--minimized", "--startup-command", action]):
                try:
                    keylight_controller.main()
                except SystemExit as exc:
                    assert exc.code == 0, exc.code

assert calls[0] == "lights.list", calls
if action == "toggle":
    assert calls.count("lights.toggle") == 1, calls
    assert timer_fired, "Controller exited before asynchronous updates could finish"
else:
    assert "lights.toggle" not in calls, calls
print(f"PASS: cold-start {action} lifecycle")
