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
3. Otherwise `enter_app()` runs: `ensure_on_path`, installs scrcpy behind the "Updating scrcpy" screen if the toolkit has no copy, builds the `Shell`, opens the Apps screen, then starts `check_updates`, `refresh_scrcpy` and `_poll_devices` as asyncio tasks.

### Tool lookup and install

- The managed copy lives in `data_dir()/platform-tools`, which is `%LOCALAPPDATA%\ADB Toolkit` on Windows. `find_tool()` prefers that copy over PATH. `Adb` and `Fastboot` resolve the path on every call, so a fresh install is used without a restart.
- `core/updates.py` parses Google's SDK feed (`repository2-3.xml`). The feed names the platforms `windows`, `macosx` and `linux`, and `HOST_OS_BY_PLATFORM` maps `sys.platform` onto those names.
- `install()` holds a module-level lock, downloads into a temp folder under the data dir, and checks the SHA-1. `install_archive()` then unpacks into a staging folder, runs `adb kill-server`, moves the old folder to `platform-tools.previous`, and moves it back if the swap fails.

### Update checks

`Window.check_updates()` runs two checks. `core/updates.py` reads Google's SDK feed for platform-tools. `core/app_updates.py` reads GitHub's latest-release endpoint for ADB Toolkit. GitHub answers 404 until the first release is published. That is stored as `Session.app_checked` with `app_release` set to `None`, not as an error. The app never replaces itself: the Updates screen opens the release page.

### Device polling

`Window._poll_devices` runs every `POLL_SECONDS` (3). Each pass calls `Session.scan()`, which runs `adb devices -l` and `fastboot devices`. `Session.update_devices()` returns whether the list changed, and the UI only redraws on a change. `_default_serial` prefers a ready adb device. Every adb command passes `-s <serial>`. `Device.is_ready` is true only for adb state `device`. Fastboot devices share the same list, with `mode == "fastboot"`.

### Screen mirroring

`core/scrcpy.py` is the only place that knows how to run scrcpy. It finds the program in the toolkit's folder, then on PATH, and starts one window per phone with `ADB` set to the toolkit's own adb. `Scrcpy.running()` checks the process, and `atexit` closes the windows on exit. scrcpy's output goes to `scrcpy.log`, which is shown when a window dies on its own. The screen section is `ui/views/mirror.py`, embedded in `AdbToolsView`. Its watcher task is what turns "window closed" into a refresh.

`core/scrcpy_install.py` downloads scrcpy. It reads GitHub's latest-release JSON, picks the asset for `sys.platform` and `platform.machine()` (`asset_prefix`), and checks the asset's `digest` (SHA-256), or `SHA256SUMS.txt` when the API gives no digest. A download without a known checksum is refused. `install_archive()` unpacks a `.zip` or `.tar.gz` into a staging folder and swaps it into `scrcpy_dir()`, keeping the old copy until the new one is in place. `Window.update_scrcpy()` runs it behind the "Updating scrcpy" screen. `enter_app()` calls it when `managed_executable()` is missing, and `refresh_scrcpy()` calls it in the background when the installed version (`scrcpy --version`) is older than the release and no mirror window is open. A failure leaves the screen up with Try again and a way out.

### Full-window screens

`SetupView` is the download screen for platform-tools and for scrcpy. It replaces `page.controls`, so the main window is off the page while it shows. `Window._covered` is true during that time, and every `shell` update (`devices_changed`, `updates_changed`) is skipped through `_shell_visible`, because updating a detached control raises. When the screen closes, `update_scrcpy` puts `shell.root` back and redraws once. Content inside such a screen needs `tight=True` on its `Column`, or the column fills the height and sits at the top.

### Blocking work from the UI

Flet runs on asyncio, so anything that touches a subprocess or the network goes through `Window.run_blocking(func, *args, on_tick=None, **kwargs)`. It runs the call in a thread and, about every 100 ms, calls `on_tick` and `page.update()`. Progress bars are driven this way.

### Screens and navigation

- Sidebar keys and `Shell.views` keys must match: `apps`, `adb`, `fastboot`, `files`, `capture`, `console`, `settings`, `updates`, `about`. To add a screen, subclass `View` in `ui/views/base.py`, register it in `Shell.views`, and add a tuple to `TOOL_ITEMS` or `APP_ITEMS` in `sidebar.py`. The sidebar also holds the device picker, so `Shell.render_device()` and `Sidebar.show_device()` are where the selected phone is drawn.
- A scrolling screen is a `ListView` with `SCROLL_PADDING`, not a scrolling `Column`, so the scrollbar does not sit on the buttons at the right edge.
- A `View` builds its controls in `__init__` and refreshes in `activate()`, which runs each time the screen opens. `on_devices_changed()` runs only for the visible screen.
- Screens swap inside an `AnimatedSwitcher`, which fades only when the content's key changes. `Shell` sets `view.control.key` from its `views` key, so keep those keys unique.
- A plain `Container` with `on_click` needs `ink=True` and `ink_color=ripple()`, or it gives no press feedback. `tests/test_shell.py` checks this for every clickable container.
- `RebootView` is the shared base for ADB Tools and Fastboot Tools. Subclasses supply the target list, `accepts`, `not_accepted_hint` and `send`.
- Apps screen: `Adb.list_packages` combines `pm list packages` (installed) with `pm list packages -s -u` (all system packages). A system package that is not installed is shown as removed, and gets a Restore button. Uninstall and restore are judged from the command's output text (`Success`, `installed for user`, `already installed`), not from the exit code.

### Theme

`ui/theme.py` defines two `Palette` dataclasses. `activate()` sets the active palette at module level, and widgets read `palette()` when they are built. Colours are therefore fixed at construction, so changing the theme rebuilds the whole `Shell` (`Window.set_theme_mode`). Do not capture colours at import time.

Type, spacing and shape come from the constants at the top of `ui/theme.py`, not literal numbers. Text is Segoe UI, the system sans, with IBM Plex Mono bundled for data. `text(..., strong=True)` gives the semibold weight. Font sizes are `TYPE_DISPLAY` (26), `TYPE_TITLE` (17), `TYPE_LABEL` (15), `TYPE_BODY` (14) and `TYPE_CAPTION` (12). Gaps and padding use the `SPACE_*` scale (4, 8, 12, 16, 24, 32). `tests/test_design_tokens.py` fails on a literal `size=` in a text or icon call, on a raw Flet button outside `widgets.py`, or on a spacing value off the scale. Controls are squared rounded rectangles: buttons, fields and navigation items use `RADIUS_CONTROL` (10) at `CONTROL_HEIGHT` (40). Chips and tags are pills (`RADIUS_PILL`). Surfaces (cards, dialogs, menus, snack bars) use `RADIUS_CARD` (16), and icon tiles use `RADIUS_TILE`. Dialogs, snack bars and the device menu pass the radius as `shape`, because Flet's defaults (28, 4) do not match.

Every visible string goes through `t()` from `ui/i18n.py`, with the English text as the key. Add the German text to `_GERMAN` in the same change. `tests/test_i18n.py` fails on a missing or an unused entry. Labels in module-level tuples are translated when the screen is built, not at import, so they must not be evaluated at import.

Build the controls from `ui/widgets.py`, not from raw Flet buttons:
- `button(kind, label, ...)` is every button. `filled` is the one main action on a screen or dialog, `outlined` is any other action, `text` is Cancel, `text_danger` is a destructive row action, and `danger` is the confirm button of a destructive dialog. `button` sets each state's colours itself (`ft.ControlState` dicts), so it does not depend on Flutter's colour scheme.
- `screen_frame(title, body, subtitle=..., icon=..., hue=..., actions=..., toolbar=...)` is a screen: a `page_header` (an icon tile in the area's hue, the title, a subtitle, and the screen's actions on the right), an optional toolbar, then a body that scrolls itself.
- `card(title, children, description=..., action=..., icon=..., hue=..., divided=...)` is a surface: a heading (title, description and action), then its children. `divided=True` puts a hairline between them. `row_item(title, description, action, icon=..., hue=..., on_click=...)` is a row inside a card. With `on_click` the whole row is pressable, such as a link.
- `tag(label, color)` is a small pill that names a state, such as Removed.
- `PillGroup(options, selected, on_pick)` is a row of choices, one selected. It is a plain `Row`, because a wrapping row stretches each pill to the full width. `scroll=True` lets a long list scroll sideways.
- `ProgressLine` is the bar and line for a long job. See Long jobs above.
- Data such as serials, versions, paths and package names is set in mono with `text(..., mono=True)`. Nothing else is mono.
- `StatusLine` is a dot and a label. Use its `set(label, color)`, because a parent's update does not send the children's colours.
- `dialog_frame` in `ui/dialogs.py` builds every dialog.

Colour has three jobs. Each area of the app owns an identity hue (`blue`, `green`, `violet`, `amber`, `rose`), set in `TOOL_ITEMS`/`APP_ITEMS` and on the reboot targets. It shows only in icons, in the tint of an `icon_tile`, and in a package's tile (`letter_hue`), never as a large fill. `accent` (teal) marks actions and selection. `signal` (amber) and `danger` (red) mark status. `tests/test_theme.py` keeps text at 4.5:1 and icons at 3:1 on both palettes, and control outlines at 3:1. Check it after changing colours. Snack bars take their label colour from `on_danger`, `on_signal` or `on_accent`.

### Persistence

`theme_mode` (light or dark), `font_scale` (small, default or large) and `language` (en or de) are stored in `settings.json` in the data dir. Each value falls back to its default on its own when it is missing or unknown. `theme.text_scale()` multiplies every text size by the font scale, and `Window.change_settings` saves a change and rebuilds the shell.

### Long jobs

Install, push, pull, sideload, flash, screenshot and recording go through `core/process.stream`. It passes each output line to a callback as it arrives. adb draws progress with carriage returns, so `` ends a line too. A `timeout` kills the command and reports exit code 124. Without one, the call waits as long as the command runs. In the UI these run through `Window.run_job`, which sets `Window.busy`. Settings changes and the platform-tools install are refused while `busy` is true, because they restart the screen or the adb server. Progress shows in a `ProgressLine`: the worker thread calls `feed`, and the UI thread calls `tick`.

Screenshots and recordings are written on the phone and then pulled, because `run()` decodes stdout as text and would corrupt a PNG.

### Console rules

`core/console.py` decides what the console runs. Only adb and fastboot run, never through a shell. The selected serial is added, and `-s`, `-t`, `-H` and `-P` are refused. Flashing, erasing, unlocking, uninstalling, installing, sideloading and commands that never finish are refused, each with a pointer to the screen that does them. It is a guard against accidents, not a sandbox.

## Flet 1.0 pitfalls

- Use `ft.run(main)`, not `ft.app`. Desktop mode needs `flet[desktop]`; plain `flet` cannot open a window.
- `SegmentedButton.selected` must be a list. A set fails msgpack serialisation and leaves the page blank.
- Button styles take per-state values as `{ft.ControlState.DEFAULT: ..., ft.ControlState.DISABLED: ...}`. A bare colour applies to every state.
- Read the new value of `SegmentedButton` and `TextField` changes from `event.data`. `event.control.selected` and `event.control.value` are stale when the event fires.
- `page.run_task` needs a live session. Use it only in synchronous click handlers. In async code, await directly or use `asyncio.ensure_future`. Calling `run_task` from startup or from the polling loop kills that task silently.
- Updating a parent does not send a child's changed colour. Call `.update()` on each changed child.
- `FilePicker` is a service. `Window.pick_files`, `pick_folder` and `pick_save_path` register it once on `page.services`. Its methods are coroutines, so call them from a click handler through `run_task`.
- Flet has no `Wrap` control. `Row(wrap=True)` stretches its children to the full width.
- Dialogs go through `page.show_dialog` and `page.pop_dialog`. Snackbars go through `Window.notify`.
- To see a screen with fake devices, pass a fake `adb` into `Session` and serve `main.py --web` from a script outside the repo. `page.take_screenshot()` returns None in web mode. The browser pane stops repainting until there is input, so send a hover or key before capturing.

## Platform notes

Windows is the target. `core/path_env.py` uses `winreg` and `ctypes` and writes `HKCU\Environment\Path` on win32 only. `core/process.py` passes `CREATE_NO_WINDOW` on Windows. Other platforms have not been run.
