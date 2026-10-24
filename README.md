# Key Light Control

Control Elgato Key Lights from a Linux desktop: power, brightness, color temperature,
custom names, and quick controls in the system tray. Discover lights automatically
on your local network using mDNS.

This is a community-maintained fork of
[sandwichfarm/keylight-control](https://github.com/sandwichfarm/keylight-control),
with local rename fixes, expanded tray controls, an included toggle command, and
Flatpak packaging. It is independent of Elgato.

![Key Light Control](assets/keylight-control-ui.png)

## Install

Flatpak packaging is included here. This fork is **not yet published on Flathub**.
Download a `keylight-control.flatpak` build artifact from a successful GitHub Actions
run, extract the artifact ZIP, and install the bundle:

```sh
flatpak install --user ./keylight-control.flatpak
flatpak run io.github.geoffbelknap.keylight-control
```

You need the Flathub remote for the KDE runtime:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

The computer and lights must share a network that permits mDNS multicast. A firewall
may need to allow mDNS (UDP 5353). No Elgato account or cloud service is needed.
Tray menus require a desktop with system tray support. The main window also works
without a tray. On GNOME, tray integration may require an AppIndicator extension.

## Toggle from your dock or a keyboard shortcut

Right-click the application launcher and choose **Toggle All Lights** on desktops
that support desktop actions. For a keyboard shortcut, bind this command in your
desktop settings:

```sh
flatpak run io.github.geoffbelknap.keylight-control --toggle
```

This starts the controller minimized if necessary, waits up to 15 seconds for
discovery, and toggles all discovered lights together. The Unix socket API must be
enabled under Settings → Advanced (it is enabled by default). The program prints
errors to stderr and returns a nonzero status when no lights are found.
On its first toggle, the process stays running as the tray controller. Subsequent
toggle invocations send a command to that instance and return immediately.

To inspect device state without changing the lights:

```sh
flatpak run io.github.geoffbelknap.keylight-control --status
```

Inside the Flatpak, `keylight-toggle` is also included as a command:

```sh
flatpak run --command=keylight-toggle io.github.geoffbelknap.keylight-control
```

## Run from source

Use Python 3.10 or newer:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python src/keylight_controller.py
python src/keylight_controller.py --toggle
```

Source and Flatpak installations store separate settings. Quit your old installation
before migrating so two controllers do not compete to control the same lights.
No automatic login startup or global shortcut is installed; configure those using
your desktop's settings if desired.

## Build and distribute

See [Flatpak build and distribution instructions](docs/FLATPAK.md).
The package uses the KDE runtime and PySide BaseApp, with pinned and hashed Python
downloads for offline builds. Permissions allow network device discovery/control,
Wayland/X11 display access, graphics acceleration, and tray integration. It does
not request access to your home directory or host command execution.

Publishing to Flathub is the route to discovery in Bazaar on Bazzite. A GitHub
release or a downloadable Flatpak alone does not create a Flathub listing.

## Tests

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 test_local_fixes.py
```

The second command requires the GUI dependencies. These checks use mock devices
and do not change physical lights.

## License and attribution

GPL-3.0-only, following the upstream README and source license declaration. See
[LICENSE](LICENSE) and [upstream documentation](docs/UPSTREAM-README.md), including
the local JSON API reference. Original development and Git history are preserved;
this fork adds packaging and local fixes. Elgato and Key Light are trademarks of
their respective owners.
