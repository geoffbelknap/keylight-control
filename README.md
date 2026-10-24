# Key Light Control

A Linux desktop app for Elgato Key Lights. Control power, brightness, and color
temperature, give lights custom names, and make quick adjustments from the system
tray. Lights are discovered automatically on the local network.

![Key Light Control](assets/keylight-control-ui.png)

## Requirements

- Linux on an Intel or AMD 64-bit PC (x86_64).
- [Flatpak](https://flatpak.org/setup/), which is included with Bazzite.
- Elgato Key Lights on the same local network as the computer.

No Elgato account is required. Settings and device names are stored locally.

## Install

**[Download the latest Flatpak](https://github.com/geoffbelknap/keylight-control/releases/latest/download/keylight-control.flatpak)**
· [Release notes and checksums](https://github.com/geoffbelknap/keylight-control/releases/latest)

Open a terminal in the folder containing `keylight-control.flatpak` and run:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user ./keylight-control.flatpak
```

Accept the prompts to install the app and its runtime dependencies. Python and Qt
are included; they do not need to be installed separately.

Launch **Key Light Control** from the application menu, or run:

```sh
flatpak run io.github.geoffbelknap.keylight-control
```

Quit any other Key Light controller before launching the app.

## Use

Use each light's power button and sliders to adjust its settings. Open the light's
menu to rename it. The system tray menu provides individual and all-light controls.

Closing the controls window keeps the app running in the tray. Choose **Quit**
from the tray menu or press **Ctrl+Q** in the controls window to exit.

Light state refreshes every 75 seconds, when controls are reopened, and before a
toggle. Each light displays its connection status. If a light goes offline, the
app checks for it again on the next refresh or interaction.

### Keyboard shortcut

Bind this command in the desktop's keyboard shortcut settings to toggle all lights:

```sh
flatpak run io.github.geoffbelknap.keylight-control --toggle
```

The command starts the app in the tray if it is not already running. Desktops
that support launcher actions also provide **Toggle All Lights** when
right-clicking the application launcher.

To print light and connection state as JSON:

```sh
flatpak run io.github.geoffbelknap.keylight-control --status
```

### Start at login

Add the following command to the desktop's startup applications:

```sh
flatpak run io.github.geoffbelknap.keylight-control --minimized
```

## Troubleshooting

- **No lights found:** check that the lights are powered and connected to the same
  network as the computer. The network must allow mDNS multicast (UDP port 5353).
  Guest Wi-Fi, VPNs, or firewall rules can prevent discovery.
- **A light is offline:** check its power and network connection, then reopen the
  controls to refresh its state. Hover over its connection status for error details.
- **The toggle shortcut fails:** check that the local API and Unix socket options
  are enabled under **Settings → Advanced**. Both are enabled by default.
- **No tray icon:** the desktop must support system tray icons. GNOME may require
  an AppIndicator extension. Reopen the app from the application menu to show the
  controls window.

## Update

Download the latest Flatpak from the link above, quit the app, and repeat the
installation command. Preferences and custom light names are preserved.

## Verify a download

Download `keylight-control.flatpak.sha256` from the same release and place it
beside `keylight-control.flatpak`. In that folder, run:

```sh
sha256sum --check keylight-control.flatpak.sha256
```

## Uninstall

```sh
flatpak uninstall --user io.github.geoffbelknap.keylight-control
```

## More documentation

- [Run from source, migrate settings, and contribute](docs/DEVELOPMENT.md)
- [Flatpak packaging and distribution](docs/FLATPAK.md)
- [Local API reference](docs/UPSTREAM-README.md#local-api)

## License and credits

Licensed under [GPL-3.0-only](LICENSE). This community-maintained fork is based on
[sandwichfarm/keylight-control](https://github.com/sandwichfarm/keylight-control)
and is independent of Elgato. Elgato and Key Light are trademarks of their
respective owners.
