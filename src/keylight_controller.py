#!/usr/bin/env python3
"""
Key Light Controller - Entry point
Minimal launcher that wires the application and starts the UI.
"""

__version__ = "1.3.1"
__license__ = "GPL-3.0"

import sys
import asyncio
import signal
import os


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Key Light Controller")
    parser.add_argument("--version", action="version", version=f"Key Light Controller {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--minimized", action="store_true", help="Start in the system tray")
    parser.add_argument("--startup-command", choices=["toggle", "status"], help=argparse.SUPPRESS)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--toggle", action="store_true", help="Toggle all lights, starting the controller if needed")
    actions.add_argument("--status", action="store_true", help="Print discovered lights as JSON")
    args = parser.parse_args()
    if args.toggle or args.status:
        from cli import main as cli_main
        sys.exit(cli_main(status=args.status))

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from utils.single_instance import SingleInstance
    from ui.main_window import KeyLightController
    from utils.system_tray import make_keylight_icon

    # Enforce single instance
    single_instance = SingleInstance()
    if single_instance.is_running():
        print("Key Light Control is already running.")
        try:
            single_instance.activate_existing()
        except Exception:
            pass
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("Key Light Control")
    app.setDesktopFileName(os.environ.get("FLATPAK_ID", "keylight-controller"))
    app.setWindowIcon(QIcon.fromTheme("io.github.geoffbelknap.keylight-control", make_keylight_icon()))
    app.setQuitOnLastWindowClosed(False)

    # Integrate asyncio event loop with Qt
    try:
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
    except ImportError:
        # Fallback: run without qasync (reduced async integration)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    controller = KeyLightController()
    if not args.minimized and not controller.prefs.get("general.launch_minimized", False):
        controller.show()

    # Graceful signal handling (SIGINT/SIGTERM) to quit cleanly
    def _handle_signal(signum, _frame):
        try:
            # Stop discovery and request app quit
            try:
                controller.quit_application()
            except Exception:
                pass
            # Stop asyncio loop if present
            try:
                loop.stop()
            except Exception:
                pass
        except Exception:
            pass

    try:
        signal.signal(signal.SIGINT, _handle_signal)
    except Exception:
        pass
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, _handle_signal)
        except Exception:
            pass

    # Allow secondary invocations to activate existing window
    def check_for_activation():
        try:
            single_instance.socket.setblocking(False)
            conn, _addr = single_instance.socket.accept()
            conn.close()
            controller.refresh_devices()
            controller.show()
            controller.raise_()
            controller.activateWindow()
        except Exception:
            pass

    activation_timer = QTimer()
    activation_timer.timeout.connect(check_for_activation)
    activation_timer.start(100)

    exit_code = 0
    if args.startup_command:
        import json
        import time
        startup_deadline = time.monotonic() + 15
        startup_devices = ()
        startup_settle_until = time.monotonic() + 1
        startup_timer = QTimer()

        def run_startup_command():
            nonlocal exit_code, startup_devices, startup_settle_until
            from cli import devices_ready
            state = controller._api.handle_request("lights.list")
            devices = tuple(device.get("mac", device.get("ip", str(index)))
                            for index, device in enumerate(state.get("devices", [])))
            if devices != startup_devices:
                startup_devices = devices
                startup_settle_until = time.monotonic() + 1
            ready = bool(devices) if args.startup_command == "status" else devices_ready(state)
            if not ready or time.monotonic() < startup_settle_until:
                if time.monotonic() < startup_deadline:
                    return
                startup_timer.stop()
                print("No Key Lights found. Check power and network access.", file=sys.stderr)
                exit_code = 1
                controller.quit_application()
                return
            startup_timer.stop()
            async def finish_command():
                nonlocal exit_code
                command = "lights.list" if args.startup_command == "status" else "lights.toggle"
                result = await controller._api.handle_request_async(command)
                print(json.dumps(result), flush=True)
                if not result.get("ok"):
                    exit_code = 1
                if args.startup_command == "status" or exit_code:
                    controller.quit_application()
            asyncio.create_task(finish_command())

        startup_timer.timeout.connect(run_startup_command)
        startup_timer.start(250)

    try:
        with loop:
            loop.run_forever()
    finally:
        single_instance.cleanup()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
