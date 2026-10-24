"""Runtime locations shared by the controller and its command-line client."""
import os
from pathlib import Path


def control_socket_path() -> str:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/keylight-{os.getuid()}"))
    if os.environ.get("FLATPAK_ID"):
        runtime = runtime / "app" / os.environ["FLATPAK_ID"]
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    return str(runtime / "keylight-control.sock")
