import os
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMainWindow
from config import DeviceConfig
from core.models import KeyLight
from ui.widgets.keylight_widget import KeyLightWidget
from utils.system_tray import create_tray_icon

app = QApplication([])
with tempfile.TemporaryDirectory() as config_dir:
    os.environ['XDG_CONFIG_HOME'] = config_dir
    window = QMainWindow()
    window.device_config = DeviceConfig()
    window.keylights = [KeyLight('Original', '127.0.0.1', mac_address='test-mac')]
    window._api = Mock()
    window.quit_application = Mock()
    window.on_tray_activated = Mock()
    with patch.object(KeyLightWidget, 'update_from_device'), patch.object(KeyLightWidget, 'load_lock_state'):
        widget = KeyLightWidget(window.keylights[0], window)
    window.keylight_widgets = [widget]
    widget.rename_device(window)
    widget._rename_dialog.name_input.setText('Desk Light')
    widget._rename_dialog.accept()
    assert widget.name_label.text() == 'Desk Light'
    assert DeviceConfig().get_label('test-mac', 'Original') == 'Desk Light'
    widget.rename_device(window)
    widget._rename_dialog.name_input.setText('Cancelled')
    widget._rename_dialog.reject()
    assert DeviceConfig().get_label('test-mac', 'Original') == 'Desk Light'
    tray = create_tray_icon(window)
    menu = tray.contextMenu()
    menu.actions()[0].trigger()
    window._api.handle_request.assert_called_with('lights.toggle', {})
    menu.actions()[1].trigger()
    window._api.handle_request.assert_called_with('lights.set', {'id': 0, 'on': True})
    menu.actions()[2].trigger()
    window._api.handle_request.assert_called_with('lights.set', {'id': 0, 'on': False})
    devices = menu.actions()[4].menu()
    device = devices.actions()[0].menu()
    assert device.title() == 'Desk Light'
    device.actions()[0].trigger()
    window._api.handle_request.assert_called_with('lights.set', {'id': 0, 'on': True})
    device.actions()[1].menu().actions()[2].trigger()
    window._api.handle_request.assert_called_with('lights.set', {'id': 0, 'brightness': 50})
    device.actions()[2].menu().actions()[4].trigger()
    window._api.handle_request.assert_called_with('lights.set', {'id': 0, 'temperature': 179})
    tray.hide()
print('PASS: rename save/cancel and persistence; tray names, power, brightness, temperature actions')
