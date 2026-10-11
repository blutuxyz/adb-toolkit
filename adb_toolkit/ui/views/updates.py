"""Updates: adb and fastboot against Google's latest platform-tools, and ADB Toolkit against its latest GitHub release."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import APP_VERSION, PROJECT_URL
from adb_toolkit.core.platform_tools import Progress, managed_binary
from adb_toolkit.core.versions import Version
from adb_toolkit.ui.theme import FONT_SEMIBOLD, ROW_PADDING, SECTION_GAP, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import hairline, icon_tile, status_dot, text, title_block

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class UpdatesView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._error = text("", size=13, color=colors.danger)
        self._progress = ft.ProgressBar(value=0, visible=False, color=colors.accent)
        self._progress_text = text("", size=13, color=colors.muted)
        self._check = ft.OutlinedButton(
            content=text("Check for updates"),
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self.window.page.run_task(self._check_for_updates),
        )

        # The dot is always laid out, so the status text does not move when its colour changes.
        self._tools_dot = status_dot(colors.muted, size=10)
        self._tools_status = text("", size=15, font=FONT_SEMIBOLD)
        self._adb_version = text("", mono=True)
        self._fastboot_version = text("", mono=True)
        self._install_label = text("Install update", color=colors.on_accent)
        self._install = ft.FilledButton(
            content=self._install_label,
            icon=ft.Icons.DOWNLOAD,
            disabled=True,
            on_click=lambda _: self.window.page.run_task(self._install_update),
        )

        self._app_dot = status_dot(colors.muted, size=10)
        self._app_status = text("", size=15, font=FONT_SEMIBOLD)
        self._app_label = text("")
        self._app_button = ft.FilledTonalButton(
            content=self._app_label,
            icon=ft.Icons.OPEN_IN_NEW,
            disabled=True,
            on_click=lambda _: self.window.page.run_task(self._open_app_release),
        )

        self.control = ft.Column(
            [
                ft.Row(
                    [title_block("Updates"), ft.Container(expand=True), self._check],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=SECTION_GAP),
                _section_header("Platform-tools", self._install),
                ft.Container(height=8),
                _status_row(self._tools_dot, self._tools_status),
                ft.Container(height=ROW_PADDING),
                hairline(),
                _tool_row("adb", str(managed_binary("adb").parent), self._adb_version, ft.Icons.TERMINAL, "green"),
                hairline(),
                _tool_row(
                    "fastboot",
                    str(managed_binary("fastboot").parent),
                    self._fastboot_version,
                    ft.Icons.FLASH_ON,
                    "violet",
                ),
                hairline(),
                ft.Container(height=SECTION_GAP),
                _section_header("ADB Toolkit", self._app_button),
                ft.Container(height=8),
                _status_row(self._app_dot, self._app_status),
                ft.Container(height=ROW_PADDING),
                hairline(),
                _tool_row("ADB Toolkit", PROJECT_URL.removeprefix("https://"), text(APP_VERSION, mono=True), ft.Icons.APPS, "accent"),
                hairline(),
                ft.Container(height=16),
                self._progress,
                ft.Container(height=8),
                self._progress_text,
                ft.Container(height=8),
                self._error,
            ],
            expand=True,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    async def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Redraw the versions and both update statuses from the session."""
        session = self.window.session
        self._adb_version.value = _version_text(session.local.adb_version)
        self._fastboot_version.value = _version_text(session.local.fastboot_version)
        self._error.value = ""
        self._paint_platform_tools()
        self._paint_app()
        self.window.update()

    def _paint_platform_tools(self) -> None:
        session = self.window.session
        colors = palette()
        if session.latest is None:
            self._tools_dot.bgcolor = colors.muted
            self._tools_status.value = "Not checked yet"
            self._set_install(enabled=False, label="Install update", icon=ft.Icons.DOWNLOAD)
        elif session.update_available:
            self._tools_dot.bgcolor = colors.signal
            self._tools_status.value = f"Update available: {session.latest}"
            self._set_install(enabled=True, label=f"Install {session.latest}", icon=ft.Icons.DOWNLOAD)
        else:
            self._tools_dot.bgcolor = colors.accent
            self._tools_status.value = "Up to date"
            self._set_install(enabled=False, label="Up to date", icon=ft.Icons.CHECK)

    def _paint_app(self) -> None:
        session = self.window.session
        colors = palette()
        release = session.app_release
        if not session.app_checked:
            self._app_dot.bgcolor = colors.muted
            self._app_status.value = "Not checked yet"
            self._set_app_button(enabled=False, label="Release page", icon=ft.Icons.OPEN_IN_NEW)
        elif release is None:
            self._app_dot.bgcolor = colors.muted
            self._app_status.value = "No release yet"
            self._set_app_button(enabled=False, label="Release page", icon=ft.Icons.OPEN_IN_NEW)
        elif session.app_update_available:
            self._app_dot.bgcolor = colors.signal
            self._app_status.value = f"Update available: {release.version}"
            self._set_app_button(enabled=True, label=f"View {release.version}", icon=ft.Icons.OPEN_IN_NEW)
        else:
            self._app_dot.bgcolor = colors.accent
            self._app_status.value = "Up to date"
            self._set_app_button(enabled=False, label="Up to date", icon=ft.Icons.CHECK)

    def _set_install(self, *, enabled: bool, label: str, icon: str) -> None:
        # The button only appears when there is an update to install. The status line says the rest.
        self._install.visible = enabled
        self._install.disabled = not enabled
        self._install.icon = icon
        self._install_label.value = label
        self._paint_install()

    def _paint_install(self) -> None:
        # A disabled filled button drops to a grey background, so its label has to change too.
        colors = palette()
        self._install_label.color = colors.muted if self._install.disabled else colors.on_accent
        self._install_label.update()

    def _set_app_button(self, *, enabled: bool, label: str, icon: str) -> None:
        self._app_button.visible = enabled
        self._app_button.disabled = not enabled
        self._app_button.icon = icon
        self._app_label.value = label

    def show_error(self, message: str) -> None:
        self._error.value = message
        self.window.update()

    async def _check_for_updates(self) -> None:
        self._set_busy(True)
        self._tools_status.value = "Checking"
        self._app_status.value = "Checking"
        self.window.update()
        error = await self.window.check_updates()
        self._set_busy(False)
        self.refresh()
        if error:
            self.show_error(error)

    async def _install_update(self) -> None:
        self._set_busy(True)
        self._progress.visible = True
        self._progress.value = None
        self._progress_text.value = "Downloading"
        self.window.update()

        def on_progress(progress: Progress) -> None:
            if progress.total:
                self._progress.value = progress.done / progress.total
                self._progress_text.value = (
                    f"{progress.done / 1_000_000:.1f} of {progress.total / 1_000_000:.1f} MB"
                )
            self.window.update()

        error = await self.window.install_platform_tools(on_progress)
        self._progress.visible = False
        self._progress_text.value = ""
        self._set_busy(False)
        self.refresh()
        if error:
            self.show_error(error)
        else:
            self.window.notify("Platform-tools updated.", success=True)

    async def _open_app_release(self) -> None:
        release = self.window.session.app_release
        if release is not None:
            await self.window.open_url(release.page_url)

    def _set_busy(self, busy: bool) -> None:
        self._check.disabled = busy
        self._install.disabled = busy
        self._app_button.disabled = busy
        self._paint_install()


def _section_header(title: str, action: ft.Control) -> ft.Row:
    return ft.Row(
        [text(title, size=18, font=FONT_SEMIBOLD), ft.Container(expand=True), action],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _status_row(dot: ft.Container, status: ft.Text) -> ft.Row:
    return ft.Row([dot, status], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _tool_row(name: str, location: str, version: ft.Text, icon: str, hue: str) -> ft.Container:
    colors = palette()
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        content=ft.Row(
            [
                icon_tile(icon, hue),
                ft.Column(
                    [
                        text(name, size=15, font=FONT_SEMIBOLD),
                        text(location, size=12, mono=True, color=colors.muted),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
                version,
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _version_text(version: Version | None) -> str:
    return str(version) if version else "Not installed"
