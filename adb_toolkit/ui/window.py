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
from adb_toolkit.core.platform_tools import PlatformToolsError, Progress, install, local_install
from adb_toolkit.core.session import Session
from adb_toolkit.core.settings import DARK
from adb_toolkit.core.updates import UpdateError, fetch_latest
from adb_toolkit.ui.dialogs import show_connect_wifi_dialog
from adb_toolkit.ui.shell import Shell
from adb_toolkit.ui.theme import (
    DARK_PALETTE,
    FONT_FILES,
    LIGHT_PALETTE,
    PALETTES,
    RADIUS_CARD,
    activate,
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
        self._polling = False
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
        setup = SetupView(self)
        self.page.controls = [setup.control]
        self.page.update()
        error = await self.install_platform_tools(setup.show_progress)
        if error:
            setup.show_error(error)
            return
        await self.enter_app()

    async def enter_app(self) -> None:
        self._add_to_path()
        self.shell = Shell(self)
        self.page.controls = [self.shell.root]
        self.page.update()
        self.shell.render_topbar()
        await self.shell.open("apps")
        # Startup runs inside the page's event loop. Background jobs go on that
        # loop directly, because page.run_task needs the session to be connected.
        asyncio.ensure_future(self.check_updates())
        if not self._polling:
            self._polling = True
            asyncio.ensure_future(self._poll_devices())

    # Theme

    def apply_theme(self) -> None:
        mode = self.session.settings.theme_mode
        colors = PALETTES[mode]
        activate(colors)
        self.page.theme = build_theme(LIGHT_PALETTE)
        self.page.dark_theme = build_theme(DARK_PALETTE)
        self.page.theme_mode = ft.ThemeMode.DARK if mode == DARK else ft.ThemeMode.LIGHT
        self.page.bgcolor = colors.background

    async def set_theme_mode(self, mode: str) -> None:
        if mode == self.session.settings.theme_mode:
            return
        self.session.set_theme_mode(mode)
        self.apply_theme()
        if self.shell is None:
            return
        current = self.shell.current
        self.shell = Shell(self)
        self.page.controls = [self.shell.root]
        self.page.update()
        self.shell.render_topbar()
        await self.shell.open(current)

    # Devices

    async def select_device(self, serial: str) -> None:
        self.session.select(serial)
        if self.shell:
            await self.shell.devices_changed()

    async def refresh_devices(self) -> None:
        devices = await asyncio.to_thread(self.session.scan)
        self.session.update_devices(devices)
        if self.shell:
            await self.shell.devices_changed()

    async def _poll_devices(self) -> None:
        while True:
            try:
                devices = await asyncio.to_thread(self.session.scan)
                if self.session.update_devices(devices) and self.shell:
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
            self.notify(f"Connected to {address}", success=True)
        else:
            self.notify(output or f"Could not connect to {address}.", error=True)
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
        if self.shell:
            self.shell.updates_changed()
        return "\n".join(errors) or None

    def _add_to_path(self) -> None:
        try:
            ensure_on_path(paths.platform_tools_dir())
        except OSError as error:
            self.notify(f"Could not add platform-tools to PATH: {error}", error=True)

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
        if error:
            background = colors.danger
        elif success:
            background = colors.green
        else:
            background = colors.text
        snack = ft.SnackBar(
            content=text(message, color=colors.background),
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
