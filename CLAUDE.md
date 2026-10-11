# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

On this Windows machine bare `python` resolves to the Microsoft Store stub, so call the venv interpreter directly. The examples are Git Bash paths; in PowerShell use `.venv\Scripts\python.exe`.

```bash
# one-time setup
py -3.14 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt

# run the desktop window
./.venv/Scripts/python.exe main.py

# serve the same UI to a browser at http://localhost:8550 (for layout checks)
./.venv/Scripts/python.exe main.py --web --port 8550

# all tests
./.venv/Scripts/python.exe -m pytest

# one file, one test, or tests matching a keyword
./.venv/Scripts/python.exe -m pytest tests/test_devices.py
./.venv/Scripts/python.exe -m pytest tests/test_devices.py::test_no_devices_gives_an_empty_list
./.venv/Scripts/python.exe -m pytest -k restore

# lint (pyflakes is the only linter configured)
./.venv/Scripts/python.exe -m pyflakes adb_toolkit tests main.py
```

There is no build or packaging step yet. The tests need no phone, no Flet window and no network: they use `tmp_path`, `monkeypatch` and fake objects.

## Architecture

`README.md` has the user-facing feature list and the file layout. This section covers how the pieces fit together.

### Two layers, one seam

- `adb_toolkit/core/` imports nothing from Flet. It runs subprocesses, touches the filesystem and the network, and parses their output. This layer is what the tests cover.
- `adb_toolkit/ui/` is Flet 1.0 code. It is checked by running the app, not by tests.
- `core/session.py` is the seam. `Session(adb=..., fastboot=..., settings_path=...)` takes its collaborators as arguments, so the UI can run against fake tools.

### Startup

`app.run()` calls `ft.run(_main)`, which builds `Window(page, Session())` and calls `start()`:

1. `apply_theme()`, then `local_install()` in a worker thread. This checks the managed copy of adb and fastboot and reads their versions.
2. If they are missing, `first_run()` shows `SetupView` and calls `install_platform_tools()`, which fetches the feed, downloads and installs, then calls `enter_app()`.
3. Otherwise `enter_app()` runs: `ensure_on_path`, builds the `Shell`, opens the Apps screen, then starts `check_updates` and `_poll_devices` as asyncio tasks.

### Tool lookup and install

- The managed copy lives in `data_dir()/platform-tools`, which is `%LOCALAPPDATA%\ADB Toolkit` on Windows. `find_tool()` prefers that copy over PATH. `Adb` and `Fastboot` resolve the path on every call, so a fresh install is used without a restart.
- `core/updates.py` parses Google's SDK feed (`repository2-3.xml`). The feed names the platforms `windows`, `macosx` and `linux`, and `HOST_OS_BY_PLATFORM` maps `sys.platform` onto those names.
- `install()` holds a module-level lock, downloads into a temp folder under the data dir, and checks the SHA-1. `install_archive()` then unpacks into a staging folder, runs `adb kill-server`, moves the old folder to `platform-tools.previous`, and moves it back if the swap fails.

### Device polling

`Window._poll_devices` runs every `POLL_SECONDS` (3). Each pass calls `Session.scan()`, which runs `adb devices -l` and `fastboot devices`. `Session.update_devices()` returns whether the list changed, and the UI only redraws on a change. `_default_serial` prefers a ready adb device. Every adb command passes `-s <serial>`. `Device.is_ready` is true only for adb state `device`. Fastboot devices share the same list, with `mode == "fastboot"`.

### Blocking work from the UI

Flet runs on asyncio, so anything that touches a subprocess or the network goes through `Window.run_blocking(func, *args, on_tick=None, **kwargs)`. It runs the call in a thread and, about every 100 ms, calls `on_tick` and `page.update()`. Progress bars are driven this way.

### Screens and navigation

- Sidebar keys and `Shell.views` keys must match: `apps`, `adb`, `fastboot`, `settings`, `updates`, `about`. To add a screen, subclass `View` in `ui/views/base.py`, register it in `Shell.views`, and add a tuple to `TOOL_ITEMS` or `APP_ITEMS` in `sidebar.py`.
- A `View` builds its controls in `__init__` and refreshes in `activate()`, which runs each time the screen opens. `on_devices_changed()` runs only for the visible screen.
- `RebootView` is the shared base for ADB Tools and Fastboot Tools. Subclasses supply the target list, `accepts`, `not_accepted_hint` and `send`.
- Apps screen: `Adb.list_packages` combines `pm list packages` (installed) with `pm list packages -s -u` (all system packages). A system package that is not installed is shown as removed, and gets a Restore button. Uninstall and restore are judged from the command's output text (`Success`, `installed for user`, `already installed`), not from the exit code.

### Theme

`ui/theme.py` defines two `Palette` dataclasses. `activate()` sets the active palette at module level, and widgets read `palette()` when they are built. Colours are therefore fixed at construction, so changing the theme rebuilds the whole `Shell` (`Window.set_theme_mode`). Do not capture colours at import time.

### Persistence

Only `theme_mode` is stored, in `settings.json` in the data dir. A missing or broken file falls back to dark.

## Flet 1.0 pitfalls

- Use `ft.run(main)`, not `ft.app`. Desktop mode needs `flet[desktop]`; plain `flet` cannot open a window.
- `SegmentedButton.selected` must be a list. A set fails msgpack serialisation and leaves the page blank.
- Read the new value of `SegmentedButton` and `TextField` changes from `event.data`. `event.control.selected` and `event.control.value` are stale when the event fires.
- `page.run_task` needs a live session. Use it only in synchronous click handlers. In async code, await directly or use `asyncio.ensure_future`. Calling `run_task` from startup or from the polling loop kills that task silently.
- Updating a parent does not send a child's changed colour. Call `.update()` on each changed child.
- Dialogs go through `page.show_dialog` and `page.pop_dialog`. Snackbars go through `Window.notify`.
- To see a screen with fake devices, pass a fake `adb` into `Session` and serve `main.py --web` from a script outside the repo. `page.take_screenshot()` returns None in web mode. The browser pane stops repainting until there is input, so send a hover or key before capturing.

## Platform notes

Windows is the target. `core/path_env.py` uses `winreg` and `ctypes` and writes `HKCU\Environment\Path` on win32 only. `core/process.py` passes `CREATE_NO_WINDOW` on Windows. Other platforms have not been run.
