# Key Light Control

Control Elgato Key Lights from a Linux desktop: power, brightness, color temperature,
custom names, and quick controls in the system tray. Discover lights automatically
on your local network using mDNS.

This is a community-maintained fork of
[sandwichfarm/keylight-control](https://github.com/sandwichfarm/keylight-control),
with local rename fixes, expanded tray controls, an included toggle command, and
Flatpak packaging. It is independent of Elgato.

![Key Light Control](assets/keylight-control-ui.png)

## Your lights stay yours

This download shares the **application**. Each person installs it on their own
computer and controls their own Elgato lights on their own local network.
The package contains the app and its dependencies; device names, discovered
addresses, and personal preferences are stored locally on each user's computer.

## Install on Linux (x86_64)

**[Download the latest Flatpak](https://github.com/geoffbelknap/keylight-control/releases/latest/download/keylight-control.flatpak)**
· [Release notes and checksums](https://github.com/geoffbelknap/keylight-control/releases/latest)

The download is public and does not require a GitHub account. Bazzite includes
Flatpak. On another distribution, [install Flatpak](https://flatpak.org/setup/)
first. This package is for Linux x86_64 (Intel/AMD 64-bit PCs).

1. Download `keylight-control.flatpak` using the link above.
2. Open a terminal in the folder containing the downloaded file.
3. Enable Flathub for runtime dependencies, then install:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user ./keylight-control.flatpak
```

Accept the prompts to install the app and any required runtime dependencies.
You do not need to install Python or Qt separately on your computer.

4. Launch **Key Light Control** from your application menu, or run:

```sh
flatpak run io.github.geoffbelknap.keylight-control
```

Quit any older Key Light controller before launching this version. The app will
automatically discover **your own lights** on your local network.

The application itself is **not yet listed on Flathub or in Bazaar search**.
Adding the Flathub remote above supplies the runtime; the app download comes
from this repository's GitHub release. After installation, it is managed locally
as a Flatpak.

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

Light state refreshes in the background every **75 seconds**, and immediately
when controls are reopened or a toggle is requested. Commands read back the
light's actual state before reporting success. Each light shows a connection
status; an offline light is checked again on the next refresh or interaction.
Failed commands are not replayed automatically after a reconnect.

Inside the Flatpak, `keylight-toggle` is also included as a command:

```sh
flatpak run --command=keylight-toggle io.github.geoffbelknap.keylight-control
```

## Updates, verification, and removal

For now, updates are manual: download the newest release, quit the app using its
tray menu or Ctrl+Q in the controls window, and repeat the install command above.
Your Flatpak settings are preserved. `flatpak update` updates available runtime
components but does not fetch new app bundles from GitHub Releases.

To verify a download, also download `keylight-control.flatpak.sha256` from the
same release, place it beside the Flatpak, and run:

```sh
sha256sum --check keylight-control.flatpak.sha256
```

To uninstall the app:

```sh
flatpak uninstall --user io.github.geoffbelknap.keylight-control
```

Preferences are stored in
`~/.var/app/io.github.geoffbelknap.keylight-control/config/keylight-control/`.
Source installations use `~/.config/keylight-control/`. If migrating from source,
quit that installation first and copy the contents of its settings directory to
the Flatpak settings directory before the first launch. Also update any old
startup entry or keyboard shortcut to use the Flatpak commands in this README.

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

These commands require the application dependencies. The recovery suite uses a
local mock HTTP server to check failures, reconnects, state refreshes, and command
ordering. These checks do not change physical lights.

## License and attribution

GPL-3.0-only, following the upstream README and source license declaration. See
[LICENSE](LICENSE) and [upstream documentation](docs/UPSTREAM-README.md), including
the local JSON API reference. Original development and Git history are preserved;
this fork adds packaging and local fixes. Elgato and Key Light are trademarks of
their respective owners.
