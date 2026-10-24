# Building the Flatpak

App ID: `io.github.geoffbelknap.keylight-control`.

Install the builder and build dependencies (the SDK and BaseApp require disk space):

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.flatpak.Builder org.kde.Sdk//6.11 io.qt.PySide.BaseApp//6.11
```

From the repository root:

```sh
flatpak run org.flatpak.Builder --user --force-clean --repo=repo \
  --install-deps-from=flathub build-dir \
  packaging/io.github.geoffbelknap.keylight-control.json
flatpak build-bundle --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo \
  repo keylight-control.flatpak io.github.geoffbelknap.keylight-control
flatpak install --user ./keylight-control.flatpak
flatpak run io.github.geoffbelknap.keylight-control
```

Both the CLI/socket tests and mocked Qt regression checks run during the build.
The startup checks also verify that a cold toggle keeps the Qt event loop alive
and that status queries never toggle lights.
Test real device discovery with `--status`; test toggling only when you intend to
change the lights. On Wayland, check the window icon and desktop action. On KDE,
also check the tray menu, closing to tray, and opening the app a second time.

## Dependencies

PySide6 comes from `io.qt.PySide.BaseApp//6.11`. The matching KDE runtime and SDK
provide Qt and Python. WebEngine and NumPy are removed by the BaseApp cleanup.

`packaging/python3-modules.json` contains the dependency versions, download URLs,
and SHA-256 hashes. To regenerate it, obtain the official Flatpak pip generator
from `flatpak/flatpak-builder-tools` (the initial generator commit is
`3d6ff6697785b52ae34db8078e0ad5188a710b1f`), then run:

```sh
uv run /path/to/flatpak-pip-generator.py \
  --runtime=org.kde.Sdk//6.11 --build-isolation --prefer-wheels=zeroconf \
  --requirements-file=packaging/requirements-flatpak.txt \
  --output=packaging/python3-modules
```

Review the changed versions and hashes and rebuild before committing the result.
Keep the BaseApp, runtime, and SDK branches aligned when upgrading Qt.

## Sandbox and configuration

Network access is required for multicast DNS discovery and the lights' HTTP APIs.
The app has no host/home filesystem permission. Settings live below the Flatpak's
`XDG_CONFIG_HOME`, normally
`~/.var/app/io.github.geoffbelknap.keylight-control/config/keylight-control/`.

The CLI and controller share a socket at
`$XDG_RUNTIME_DIR/app/$FLATPAK_ID/keylight-control.sock`. The activation socket and
instance lock also live there. Source installations use
`$XDG_RUNTIME_DIR/keylight-control.sock`. Without `XDG_RUNTIME_DIR`, the source
installation uses a per-user directory under `/tmp`.

The optional upstream HTTP API remains disabled by default. The bundled toggle
uses the owner-only Unix socket. Source-install scripts targeting the old socket
path need to use `flatpak run … --toggle` after migration.

## GitHub releases

The Flatpak workflow builds pull requests and pushes and uploads a downloadable
bundle. Pushing a `v*` tag additionally creates a **draft** GitHub release with the
Flatpak attached. Review it and publish it when the package is ready for users.

## Flathub and Bazaar

Bazaar searches configured Flatpak remotes, including Flathub. For normal
discovery on Bazzite, submit this app to Flathub; GitHub artifacts alone will not
appear in search.

Before submission:

1. Test the installed package on real lights and supported desktops, and publish
   a stable source tag and release. Confirm all included material is licensed.
2. Replace the app module's local `dir` source with the public repository URL and
   an immutable release commit. Keep Python modules as pinned, hashed downloads.
   Paths in the submitted manifest must refer to the source archive or files
   included with the Flathub submission.
3. Check the current requirements, metadata, screenshot, app ID ownership, and
   submission policies. This is a fork; disclose the upstream relationship and
   verify whether an existing listing or upstream coordination affects eligibility.
4. Run the Flathub manifest and repository linters and resolve their findings.
   Local repositories using the original screenshot URL report screenshot
   mirroring errors. Flathub builds mirror screenshots to their media service;
   verify those checks with the Flathub build before submission approval.
5. Prepare a submission on the `new-pr` branch of `flathub/flathub`, following the
   official submission process. Approval and publication are separate from this
   repository's CI builds.

References:

- https://docs.flathub.org/docs/for-app-authors/submission
- https://docs.flathub.org/docs/for-app-authors/requirements
- https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines
- https://github.com/flathub/io.qt.PySide.BaseApp/tree/wiki
- https://usebazaar.org/
