import fcntl
from pathlib import Path
import socket

from utils.paths import control_socket_path


class SingleInstance:
    """Ensures only one instance of the application runs."""

    def __init__(self):
        self._path = Path(control_socket_path()).with_name("activation.sock")
        self._lock = None
        self.socket = None

    def is_running(self) -> bool:
        """Check if another instance is already running."""
        self._lock = self._path.with_suffix(".lock").open("a")
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            self._lock = None
            return True
        self._path.unlink(missing_ok=True)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(self._path))
        self._path.chmod(0o600)
        self.socket.listen(8)
        self.socket.setblocking(False)
        return False

    def activate_existing(self):
        """Ask the existing application to show its window."""
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(2)
            client.connect(str(self._path))

    def cleanup(self) -> None:
        """Clean up the socket."""
        if self.socket:
            self.socket.close()
            self.socket = None
        if self._lock:
            self._path.unlink(missing_ok=True)
            self._lock.close()
            self._lock = None

