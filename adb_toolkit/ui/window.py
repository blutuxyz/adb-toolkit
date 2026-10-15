"""The app window: startup, first-run setup, device polling and background jobs."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Callable
from typing import Any, TypeVar

import flet as ft

from adb_toolkit.config import APP_NAME
from adb_toolkit.core import paths
from adb_toolkit.core.app_updates import fetch_latest_release
from adb_toolkit.core.path_env import ensure_on_path
from adb_toolkit.core import scrcpy_install
from adb_toolkit.core.platform_tools import PlatformToolsError, Progress, install, local_install
from adb_toolkit.core.scrcpy import managed_executable
from adb_toolkit.core.scrcpy_install import RemoteScrcpy, ScrcpyInstallError
from adb_toolkit.core.session import Session
from adb_toolkit.core.settings import DARK, FONT_SCALES
from adb_toolkit.core.updates import UpdateError, fetch_latest
from adb_toolkit.core.versions import needs_update
from adb_toolkit.ui.dialogs import show_connect_wifi_dialog
from adb_toolkit.ui.i18n import activate_language, t
from adb_toolkit.ui.shell import Shell
from adb_toolkit.ui.theme import (
    DARK_PALETTE,
    FONT_FILES,
    LIGHT_PALETTE,
    PALETTES,
    RADIUS_CARD,
    activate,
    activate_text_scale,
    build_theme,
    palette,
)
from adb_toolkit.ui.views.setup import SetupView
from adb_toolkit.ui.widgets import text

log = logging.getLogger(__name__)

POLL_SECONDS = 3
_WIFI_CONNECTED = re.compile(r"connected to", re.IGNORECASE)
T = TypeVar("T")


class Window:
    def __init__(self, page: ft.Page, session: Session) -> None:
        self.page = page
        self.session = session
        self.shell: Shell | None = None
        self._launcher: ft.UrlLauncher | None = None
        self._file_picker: ft.FilePicker | None = None
        self._jobs = 0  # long jobs running now; settings do not change while one runs
        self._polling = False
        self._covered = False  # a full-window screen has replaced the main window, which is then off the page
        page.title = APP_NAME
        page.padding = 0
        page.spacing = 0
        page.fonts = FONT_FILES
        page.window.width = 1240
        page.window.height = 800
        page.window.min_width = 1000
        page.window.min_height = 660

    def update(self) -> None:
        self.page.update()

    # Startup

    async def start(self) -> None:
        self.apply_theme()
        self.session.local = await asyncio.to_thread(local_install)
        if self.session.local.installed:
            await self.enter_app()
        else:
            await self.first_run()

    async def first_run(self) -> None:
        setup = SetupView(
            self,
            title=t("Set up platform-tools"),
            body=t("Downloads Google's adb and fastboot and adds them to your PATH."),
            retry=lambda: self.page.run_task(self.first_run),
        )
        self.page.controls = [setup.control]
        self.page.update()
        error = await self.install_platform_tools(setup.show_progress)
        if error:
            setup.show_error(error)
            return
        await self.enter_app()

    async def enter_app(self) -> None:
        self._add_to_path()
        if not managed_executable().is_file():
            await self.update_scrcpy()
        self.shell = Shell(self)
        self.page.controls = [self.shell.root]
        self.page.update()
        self.shell.render_device()
        await self.shell.open("apps")
        # Startup runs inside the page's event loop. Background jobs go on that
        # loop directly, because page.run_task needs the session to be connected.
        asyncio.ensure_future(self.check_updates())
        asyncio.ensure_future(self.refresh_scrcpy())
        if not self._polling:
            self._polling = True
            asyncio.ensure_future(self._poll_devices())

    # Theme

    def apply_theme(self) -> None:
        settings = self.session.settings
        mode = settings.theme_mode
        colors = PALETTES[mode]
        activate(colors)
        activate_text_scale(FONT_SCALES[settings.font_scale])
        activate_language(settings.language)
        self.page.theme = build_theme(LIGHT_PALETTE)
        self.page.dark_theme = build_theme(DARK_PALETTE)
        self.page.theme_mode = ft.ThemeMode.DARK if mode == DARK else ft.ThemeMode.LIGHT
        self.page.bgcolor = colors.background

    async def set_theme_mode(self, mode: str) -> None:
        if mode == self.session.settings.theme_mode:
            return
        await self.change_settings(theme_mode=mode)

    async def change_settings(self, **changes: str) -> None:
        """Save new settings and rebuild the shell, so every screen is drawn with them.

        Refused while a job runs, because the job's controls would be thrown away.
        """
        if self.busy:
            self.notify(t("Wait for the running task to finish."), error=True)
            return
        self.session.set_settings(**changes)
        self.apply_theme()
        if self.shell is None:
            return
        current = self.shell.current
        self.shell = Shell(self)
        self.page.controls = [self.shell.root]
        self.page.update()
        self.shell.render_device()
        await self.shell.open(current)

    # Devices

    @property
    def _shell_visible(self) -> bool:
        return self.shell is not None and not self._covered

    async def select_device(self, serial: str) -> None:
        self.session.select(serial)
        if self._shell_visible:
            await self.shell.devices_changed()

    async def refresh_devices(self) -> None:
        devices = await asyncio.to_thread(self.session.scan)
        self.session.update_devices(devices)
        if self._shell_visible:
            await self.shell.devices_changed()

    async def _poll_devices(self) -> None:
        while True:
            try:
                devices = await asyncio.to_thread(self.session.scan)
                if self.session.update_devices(devices) and self._shell_visible:
                    await self.shell.devices_changed()
            except Exception:  # one failed pass must not stop the polling for good
                log.exception("Device scan failed")
            await asyncio.sleep(POLL_SECONDS)

    def connect_over_wifi_dialog(self) -> None:
        show_connect_wifi_dialog(self.page, lambda address: self.page.run_task(self.connect_over_wifi, address))

    async def connect_over_wifi(self, address: str) -> None:
        result = await self.run_blocking(self.session.adb.connect, address)
        output = result.output
        if result.ok and _WIFI_CONNECTED.search(output) and "failed" not in output.lower():
            self.notify(t("Connected to {address}", address=address), success=True)
        else:
            self.notify(output or t("Could not connect to {address}.", address=address), error=True)
        await self.refresh_devices()

    # Platform-tools

    async def install_platform_tools(self, on_progress: Callable[[Progress], None] | None = None) -> str | None:
        """Download the latest platform-tools and install them. Returns an error message, or None on success."""
        progress = Progress()

        def record(done: int, total: int) -> None:
            progress.done, progress.total = done, total

        tick = (lambda: on_progress(progress)) if on_progress else None
        try:
            remote = await asyncio.to_thread(fetch_latest)
            self.session.remote = remote
            await self.run_blocking(install, remote, record, on_tick=tick)
        except (UpdateError, PlatformToolsError) as error:
            return str(error)
        self.session.local = await asyncio.to_thread(local_install)
        self._add_to_path()
        return None

    # scrcpy

    async def update_scrcpy(self, remote: RemoteScrcpy | None = None) -> bool:
        """Show the 'Updating scrcpy' screen while scrcpy is downloaded and installed. Returns True on success.

        The screen replaces the main window while it runs, which also works before that window exists.
        When a download fails the screen offers another try, or a way out that keeps what was there.
        """
        decision: asyncio.Future[bool] | None = None

        def decide(retry: bool) -> None:
            if decision is not None and not decision.done():
                decision.set_result(retry)

        first_time = not managed_executable().is_file()
        screen = SetupView(
            self,
            title=t("Updating scrcpy"),
            body=t("Downloads scrcpy so the phone's screen can be mirrored and controlled."),
            retry=lambda: decide(True),
            skip=lambda: decide(False),
            skip_label=t("Continue without scrcpy") if first_time else t("Keep the current version"),
        )
        self._covered = True
        self.page.controls = [screen.control]
        self.page.update()
        progress = Progress()

        def record(done: int, total: int) -> None:
            progress.done, progress.total = done, total

        try:
            while True:
                progress.done = progress.total = 0
                try:
                    if remote is None:
                        remote = await asyncio.to_thread(scrcpy_install.fetch_latest)
                    await self.run_blocking(
                        scrcpy_install.install, remote, record, on_tick=lambda: screen.show_progress(progress)
                    )
                    return True
                except ScrcpyInstallError as error:
                    log.warning("scrcpy install failed: %s", error)
                    decision = asyncio.get_running_loop().create_future()
                    screen.show_error(str(error))
                    if not await decision:
                        return False
                    screen.reset()
        finally:
            self._covered = False
            if self.shell:
                # Without a main window yet, the screen stays until enter_app builds one.
                self.page.controls = [self.shell.root]
                self.page.update()
                await self.shell.devices_changed()
                self.shell.updates_changed()
                self.shell.scrcpy_changed()

    async def refresh_scrcpy(self) -> None:
        """Update the toolkit's copy of scrcpy when GitHub has a newer release. Quiet when there is nothing to do."""
        executable = managed_executable()
        if not executable.is_file():
            return
        installed = await asyncio.to_thread(scrcpy_install.installed_version, executable)
        if installed is None:
            return  # a copy that does not report a version is left as it is
        try:
            remote = await asyncio.to_thread(scrcpy_install.fetch_latest)
        except ScrcpyInstallError as error:
            log.warning("scrcpy update check failed: %s", error)
            return
        # Windows will not replace the program while a mirror window has it open.
        if needs_update(installed, remote.version) and not self.session.scrcpy.any_running():
            await self.update_scrcpy(remote)

    async def check_updates(self) -> str | None:
        """Look up the latest platform-tools and ADB Toolkit releases. Returns the errors, one per line, or None."""
        errors: list[str] = []
        try:
            self.session.remote = await asyncio.to_thread(fetch_latest)
        except UpdateError as error:
            log.warning("Platform-tools update check failed: %s", error)
            errors.append(str(error))
        try:
            self.session.app_release = await asyncio.to_thread(fetch_latest_release)
            self.session.app_checked = True
        except UpdateError as error:
            log.warning("App update check failed: %s", error)
            errors.append(str(error))
        if self._shell_visible:
            self.shell.updates_changed()
        return "\n".join(errors) or None

    def _add_to_path(self) -> None:
        try:
            ensure_on_path(paths.platform_tools_dir())
        except OSError as error:
            self.notify(t("Could not add platform-tools to PATH: {error}", error=error), error=True)

    # Helpers for screens

    @property
    def busy(self) -> bool:
        """True while a long job (install, transfer, sideload, flash) is running."""
        return self._jobs > 0

    async def run_job(self, func: Callable[..., T], *args: Any, on_tick: Callable[[], None] | None = None,
                      **kwargs: Any) -> T:
        """run_blocking for a long job. While it runs, the busy flag is set and settings are locked."""
        self._jobs += 1
        try:
            return await self.run_blocking(func, *args, on_tick=on_tick, **kwargs)
        finally:
            self._jobs -= 1

    def _picker(self) -> ft.FilePicker:
        # Created on first use and registered as a page service, the way UrlLauncher is.
        if self._file_picker is None:
            self._file_picker = ft.FilePicker()
            self.page.services.append(self._file_picker)
            self.page.update()
        return self._file_picker

    async def pick_files(self, *, title: str, extensions: list[str] | None) -> list[str]:
        """Let the user choose one file. Returns its path, or an empty list if they cancel."""
        picked = await self._picker().pick_files(dialog_title=title, allowed_extensions=extensions)
        return [item.path for item in picked or [] if item.path]

    async def pick_folder(self, title: str) -> str | None:
        return await self._picker().get_directory_path(dialog_title=title)

    async def pick_save_path(self, *, title: str, file_name: str, extensions: list[str]) -> str | None:
        return await self._picker().save_file(dialog_title=title, file_name=file_name, allowed_extensions=extensions)

    # Helpers for screens

    async def run_blocking(
        self,
        func: Callable[..., T],
        *args: Any,
        on_tick: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> T:
        """Run a blocking call in a worker thread and keep the UI responsive while it works.

        `on_tick` runs about every 100 ms, which is how progress bars update.
        """
        future = asyncio.ensure_future(asyncio.to_thread(func, *args, **kwargs))
        while True:
            done, _ = await asyncio.wait({future}, timeout=0.1)
            if done:
                return future.result()
            if on_tick is not None:
                on_tick()
                self.page.update()

    def notify(self, message: str, *, error: bool = False, success: bool = False) -> None:
        colors = palette()
        # Each fill comes with the label colour that reads on it.
        if error:
            background, label = colors.danger, colors.on_danger
        elif success:
            background, label = colors.accent, colors.on_accent
        else:
            background, label = colors.text, colors.background
        snack = ft.SnackBar(
            content=text(message, color=label),
            bgcolor=background,
            show_close_icon=True,
            duration=5000,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        )
        self.page.overlay[:] = [item for item in self.page.overlay if not isinstance(item, ft.SnackBar)]
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    async def open_url(self, url: str) -> None:
        if self._launcher is None:
            self._launcher = ft.UrlLauncher()
            self.page.services.append(self._launcher)
            self.page.update()
        await self._launcher.launch_url(url)
