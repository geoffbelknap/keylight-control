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

**[Install Key Light Control](https://geoffbelknap.github.io/keylight-control/keylight-control.flatpakref)**
· [Release notes](https://github.com/geoffbelknap/keylight-control/releases/latest)

Open the installation link with your software manager, or run:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-add --user --if-not-exists keylight-control https://geoffbelknap.github.io/keylight-control/keylight-control.flatpakrepo
flatpak install --user keylight-control io.github.geoffbelknap.keylight-control//master
```

Accept the prompts to install the app and its runtime dependencies. Python and Qt
are included; they do not need to be installed separately.

If you previously installed a downloaded bundle or a local build, follow the
[one-time migration](docs/UPDATES.md#migrate-an-existing-installation) to receive
updates from the maintained repository. Preferences and device names are preserved.

Launch **Key Light Control** from the application menu, or run:

```sh
flatpak run io.github.geoffbelknap.keylight-control
```

Quit any other Key Light controller before launching the app.

## Use

Use each light's power button and sliders to adjust its settings. Open the light's
menu to rename it. The system tray menu provides individual and all-light power
controls, brightness presets, and color temperature presets using saved light names.

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

Use your desktop's software updater, or run:

```sh
flatpak update --user io.github.geoffbelknap.keylight-control
```

Updates are verified against the release signing key. Quit and reopen the app
after an update to use the new version. Preferences and custom light names are
preserved.

## Verify a download

For manual installation, [GitHub releases](https://github.com/geoffbelknap/keylight-control/releases/latest)
also provide `keylight-control.flatpak` and `keylight-control.flatpak.sha256`.
Download both from the same release, place them together, and run:

```sh
sha256sum --check keylight-control.flatpak.sha256
```

After installing a manual bundle, use the one-time migration above to ensure
future updates use the maintained repository.

## Uninstall

```sh
flatpak uninstall --user io.github.geoffbelknap.keylight-control
```

## More documentation

- [Run from source, migrate settings, and contribute](docs/DEVELOPMENT.md)
- [Flatpak packaging and distribution](docs/FLATPAK.md)
- [Maintained update repository rollout and migration](docs/UPDATES.md)
- [Local API reference](docs/UPSTREAM-README.md#local-api)

## License and credits

Licensed under [GPL-3.0-only](LICENSE). This community-maintained fork is based on
[sandwichfarm/keylight-control](https://github.com/sandwichfarm/keylight-control)
and is independent of Elgato. Elgato and Key Light are trademarks of their
respective owners.
