# ADB Toolkit

One desktop window for `adb` and `fastboot`. Written in Python with
[Flet](https://flet.dev) and its Material 3 controls.

## What it does

- **Platform-tools on first start.** Downloads Google's platform-tools, checks the
  SHA-1 from Google's SDK feed, unpacks them into `%LOCALAPPDATA%\ADB Toolkit`
  and adds that folder to your user PATH.
- **scrcpy, downloaded for you.** On first start, and whenever GitHub has a newer
  release, an "Updating scrcpy" screen downloads scrcpy, checks its SHA-256 and
  unpacks it into `%LOCALAPPDATA%\ADB Toolkit\scrcpy`.
- **Updates.** Compares the installed adb and fastboot with the latest release and
  installs the new one when you ask. It also checks GitHub for a newer ADB Toolkit
  release and links to its release page.
- **Device picker and Wi-Fi connect** at the top of the sidebar. ADB and fastboot devices
  are listed together, with their state.
- **Apps.** Lists the packages on the selected phone. Uninstall apps, or restore
  system apps that were removed earlier.
- **ADB Tools and Fastboot Tools.** Reboot to system, recovery or bootloader. ADB
  Tools also mirrors the phone's screen and sends mouse and keyboard input with scrcpy.
- **Files.** Install an APK from a file picker. Send a file to the phone, or get one from it.
- **Capture.** Take a screenshot, or record the screen for 10 s, 30 s or 3 min, and save it to the PC.
- **Console.** Type an adb or fastboot command and read its output. Commands that flash, erase,
  unlock, install or never finish are refused, with a pointer to the screen that does them safely.
- **Sideload and flashing.** ADB Tools sideloads a ROM or update ZIP. Fastboot Tools flashes one
  partition, and makes you type the partition name before it runs.
- **Settings.** Light or dark theme, each shown with a drawing of the layout. Text size
  (small, default, large), and language (English or German).
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
    app_updates.py         read GitHub's latest ADB Toolkit release
    path_env.py            PATH for this process and the Windows user PATH
    adb.py, fastboot.py    command wrappers
    devices.py, packages.py  parsers for device and package lists
    session.py             selected device, versions, settings
    scrcpy.py              find and run scrcpy, one mirror window per phone
    scrcpy_install.py      download, verify and install scrcpy from GitHub
    settings.py, paths.py, versions.py, process.py (also streams long commands)
    console.py             rules for the command console
  ui/
    theme.py               palettes and the Material theme
    window.py              startup, first-run setup, polling, background jobs
    shell.py               sidebar + content area
    sidebar.py, dialogs.py, widgets.py, i18n.py (English and German text)
    views/                 one module per screen
assets/fonts/              IBM Plex Mono (SIL Open Font License, see OFL.txt)
tests/                     pytest suite
```

## Things to know

- **PATH changes.** On Windows the platform-tools folder is appended to your user
  PATH (`HKCU\Environment\Path`). To undo it, remove that entry in the Windows
  environment variable settings.
- **Uninstalling system apps.** This runs `pm uninstall -k --user 0`. The app is
  removed for user 0 only and its data stays on the phone. Restore runs
  `cmd package install-existing --user 0`. No root is needed.
- **App icons.** adb does not give out app icons, so each app gets a generic icon on
  a tile in a colour picked from its package name.
- **scrcpy.** The toolkit downloads scrcpy from its GitHub releases into
  `%LOCALAPPDATA%\ADB Toolkit\scrcpy` and prefers that copy over one on PATH. If the
  download fails, the "Updating scrcpy" screen offers another try or a way to carry on
  without it, and the screen section has an Install scrcpy button. The update check
  skips a run while a mirror window is open, because Windows will not replace a
  program that is running. The toolkit passes its own adb to scrcpy and closes any
  mirror windows when it exits.
- **Not built yet:** a stop button for long transfers, and browsing folders on the phone.
  Messages from adb and fastboot itself stay in English.
