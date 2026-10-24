"""Control the running application without creating another Qt window."""
import json
import os
from pathlib import Path
import socket
import sys
import time

from utils.paths import control_socket_path


def request(command):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(5)
        sock.connect(control_socket_path())
        sock.sendall((json.dumps({"command": command}) + "\n").encode())
        with sock.makefile("r") as stream:
            result = json.loads(stream.readline())
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Controller request failed"))
    return result


def main(status=False):
    try:
        try:
            state = request("lights.list")
        except (FileNotFoundError, ConnectionRefusedError):
            # Keep the controller as the Flatpak's main process. A detached child
            # would be terminated when the original command exits its sandbox.
            launch = [sys.executable]
            if not getattr(sys, "frozen", False):
                launch.append(str(Path(__file__).with_name("keylight_controller.py")))
            launch += ["--minimized", "--startup-command", "status" if status else "toggle"]
            os.execv(sys.executable, launch)
        deadline = time.monotonic() + 15
        while not devices_ready(state) and time.monotonic() < deadline:
            time.sleep(0.25)
            try:
                state = request("lights.list")
            except (FileNotFoundError, ConnectionRefusedError):
                continue
        if not devices_ready(state):
            raise RuntimeError(
                "No Key Lights found. Check power, network access, and that the "
                "controller's Unix socket API is enabled in Settings > Advanced."
            )
        print(json.dumps(state if status else request("lights.toggle")))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def devices_ready(state):
    devices = state.get("devices", [])
    return bool(devices) and all(device.get("ready", True) for device in devices)
