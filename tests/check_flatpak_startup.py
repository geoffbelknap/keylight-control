"""Run on stdin inside an installed Flatpak, including an older release.

This deliberately uses the deployed Platform runtime, not the build SDK. It
does not instantiate the controller, discover devices, or change any lights.
"""
import sys

import PySide6
from PySide6.QtCore import QTimer, qVersion
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

sys.path.insert(0, '/app/share/keylight-control')
import aiohttp
import qasync
import zeroconf
from ui.main_window import KeyLightController
from utils.system_tray import make_keylight_icon

print(f'PySide {PySide6.__version__}; Qt {qVersion()}', flush=True)
app = QApplication([])
app.setWindowIcon(QIcon(make_keylight_icon()))
loop = qasync.QEventLoop(app)
QTimer.singleShot(50, loop.stop)
with loop:
    loop.run_forever()
print('PASS: installed Flatpak Qt imports, icon, and event loop', flush=True)
