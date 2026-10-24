# Running from source and contributing

## Run from source

Python 3.10 or newer is required.

```sh
git clone https://github.com/geoffbelknap/keylight-control.git
cd keylight-control
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python src/keylight_controller.py
```

The same command-line options are available from source:

```sh
python src/keylight_controller.py --toggle
python src/keylight_controller.py --status
```

## Settings and migration

Source installations store settings in `~/.config/keylight-control/`.
Flatpak installations store settings in
`~/.var/app/io.github.geoffbelknap.keylight-control/config/keylight-control/`.

To migrate from source to Flatpak, quit the source installation, create the
Flatpak settings directory if necessary, and copy the contents of the source
settings directory into it before the first launch. Update any startup entry
and keyboard shortcut to use the Flatpak commands in the README. Run one
controller installation at a time.

## Tests

With the virtual environment active and the application dependencies installed:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python test_local_fixes.py
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/check_startup_lifecycle.py toggle
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/check_startup_lifecycle.py status
```

The recovery suite uses a local mock HTTP server to check failures, reconnects,
state refreshes, and command ordering. These checks do not control physical lights.

## Packaging and releases

See [Flatpak packaging and distribution](FLATPAK.md) for runtime dependencies,
offline build sources, sandbox permissions, release automation, and distribution
requirements.
