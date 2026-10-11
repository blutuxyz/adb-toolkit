# ADB Toolkit

One desktop window for `adb` and `fastboot`. Written in Python with
[Flet](https://flet.dev) and its Material 3 controls.

## What it does

- **Platform-tools on first start.** Downloads Google's platform-tools, checks the
  SHA-1 from Google's SDK feed, unpacks them into `%LOCALAPPDATA%\ADB Toolkit`
  and adds that folder to your user PATH.
- **Updates.** Compares the installed adb and fastboot with the latest release and
  installs the new one when you ask.
- **Device picker and Wi-Fi connect** in the top bar. ADB and fastboot devices are
  listed together, with their state.
- **Apps.** Lists the packages on the selected phone. Uninstall apps, or restore
  system apps that were removed earlier.
- **ADB Tools and Fastboot Tools.** Reboot to system, recovery or bootloader.
- **Settings.** Light or dark theme, each shown with a drawing of the layout.
- **About.**

## Run it from source

```bash
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On Windows, `python main.py --web` serves the same UI to a browser on
`localhost:8550`. It is handy for checking layout changes without opening the
native window.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
python -m pyflakes adb_toolkit tests main.py
```

The tests cover the parsers, the platform-tools installer (with a generated zip and
a faked download), PATH handling, settings and the session logic. The UI is checked
by running the app and looking at the screens.

## Project layout

```
main.py                    entry point (desktop window, or --web)
adb_toolkit/
  config.py                names, links, Google download endpoints
  app.py                   starts the Flet page and the Window
  core/                    no UI imports
    platform_tools.py      install, verify, locate adb and fastboot
    updates.py             read Google's SDK feed for the latest release
    path_env.py            PATH for this process and the Windows user PATH
    adb.py, fastboot.py    command wrappers
    devices.py, packages.py  parsers for device and package lists
    session.py             selected device, versions, settings
    settings.py, paths.py, versions.py, process.py
  ui/
    theme.py               palettes and the Material theme
    window.py              startup, first-run setup, polling, background jobs
    shell.py               sidebar + top bar + content area
    sidebar.py, topbar.py, dialogs.py, widgets.py
    views/                 one module per screen
assets/fonts/              IBM Plex (SIL Open Font License, see OFL.txt)
tests/                     pytest suite
```

## Things to know

- **PATH changes.** On Windows the platform-tools folder is appended to your user
  PATH (`HKCU\Environment\Path`). To undo it, remove that entry in the Windows
  environment variable settings.
- **Uninstalling system apps.** This runs `pm uninstall -k --user 0`. The app is
  removed for user 0 only and its data stays on the phone. Restore runs
  `cmd package install-existing --user 0`. No root is needed.
- **App icons.** adb does not give out app icons, so each app gets a letter tile
  for now.
- **Not built yet:** install APK, sideload ROM, send file, custom command, screen
  mirroring with scrcpy, flashing firmware, language selection and font size.
