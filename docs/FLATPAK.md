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

Public releases at https://github.com/geoffbelknap/keylight-control/releases
provide `keylight-control.flatpak` and a SHA-256 checksum. These downloads do not
require GitHub sign-in. The README's installation instructions use those assets.

The Flatpak workflow also builds pull requests and pushes and uploads a
downloadable CI artifact; those artifact downloads require GitHub sign-in. Pushing a `v*` tag additionally creates a **draft** GitHub release with the
Flatpak attached. Before publishing, confirm the draft targets the tested source commit and that
its attached bundle comes from that commit's successful build. Generate the
checksum from the exact attached file, update the release notes, and then publish
the draft. If a draft predates later fixes, replace its assets before publication.

## Flathub and Bazaar

Bazaar searches configured Flatpak remotes, including Flathub. For normal
discovery on Bazzite, submit this app to Flathub; GitHub artifacts alone will not
appear in search.

The current Flathub requirements prohibit AI-generated or AI-assisted manifests
and AI agents opening or automating submission PRs. They also require disclosure
of AI-generated application code, documentation, packaging, and other material.
Read the current policy before planning a submission:
https://docs.flathub.org/docs/for-app-authors/requirements#generative-ai-policy

The generated file in `packaging/flathub/` is a local build experiment, **not an
eligible Flathub submission manifest**. A human maintainer would need to
independently author the submission manifest, disclose the generated material in
this project, and handle the submission and review directly.

Before a human-led submission, test the installed release on real lights and
supported desktops, confirm licensing and app ID ownership, check upstream and
fork/duplicate eligibility, and run Flathub's build and metadata validation. Local
repositories can report screenshot-mirroring findings that must be resolved or
checked in the Flathub build environment. Direct GitHub distribution does not
require Flathub submission.

References:

- https://docs.flathub.org/docs/for-app-authors/submission
- https://docs.flathub.org/docs/for-app-authors/requirements
- https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines
- https://github.com/flathub/io.qt.PySide.BaseApp/tree/wiki
- https://usebazaar.org/
