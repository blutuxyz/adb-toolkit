"""Updates: the installed adb and fastboot versions, and the latest release from Google."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.platform_tools import Progress, managed_binary
from adb_toolkit.core.versions import Version
from adb_toolkit.ui.theme import FONT_SEMIBOLD, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import hairline, text, title_block

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class UpdatesView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._dot = ft.Container(width=10, height=10, border_radius=5, visible=False)
        self._status = text("", size=15, font=FONT_SEMIBOLD)
        self._detail = text("", size=13, color=colors.muted)
        self._adb_version = text("", mono=True)
        self._fastboot_version = text("", mono=True)
        self._error = text("", size=13, color=colors.danger)
        self._progress = ft.ProgressBar(value=0, visible=False, color=colors.accent)
        self._progress_text = text("", size=13, color=colors.muted)
        self._check = ft.OutlinedButton(
            content=text("Check for updates"),
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self.window.page.run_task(self._check),
        )
        self._install = ft.FilledButton(
            content=text("Install update", color=colors.on_accent),
            icon=ft.Icons.DOWNLOAD,
            disabled=True,
            on_click=lambda _: self.window.page.run_task(self._install_update),
        )

        self.control = ft.Column(
            [
                title_block(
                    "Updates",
                    "Keep adb and fastboot current. Downloads come from Google and are checked against their SHA-1.",
                ),
                ft.Container(height=28),
                ft.Row(
                    [self._dot, ft.Column([self._status, self._detail], spacing=4, tight=True)],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=20),
                hairline(),
                _tool_row("adb", self._adb_version),
                hairline(),
                _tool_row("fastboot", self._fastboot_version),
                hairline(),
                ft.Container(height=20),
                ft.Row([self._check, self._install], spacing=12),
                ft.Container(height=16),
                self._progress,
                ft.Container(height=6),
                self._progress_text,
                ft.Container(height=6),
                self._error,
            ],
            expand=True,
            spacing=0,
        )

    async def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Redraw the versions and the update status from the session."""
        session = self.window.session
        colors = palette()
        self._adb_version.value = _version_text(session.local.adb_version)
        self._fastboot_version.value = _version_text(session.local.fastboot_version)
        self._error.value = ""
        self._dot.visible = session.latest is not None

        if session.latest is None:
            self._status.value = "Not checked yet"
            self._detail.value = "Check for updates to compare with Google's latest release."
            self._set_install(enabled=False, label="Install update", icon=ft.Icons.DOWNLOAD)
        elif session.update_available:
            self._dot.bgcolor = colors.signal
            self._status.value = f"Update available: {session.latest}"
            self._detail.value = "Installing replaces adb and fastboot in the toolkit's own folder."
            self._set_install(enabled=True, label=f"Install {session.latest}", icon=ft.Icons.DOWNLOAD)
        else:
            self._dot.bgcolor = colors.accent
            self._status.value = "Up to date"
            self._detail.value = f"Platform-tools {session.latest} is the latest release."
            self._set_install(enabled=False, label="Up to date", icon=ft.Icons.CHECK)
        self.window.update()

    def _set_install(self, *, enabled: bool, label: str, icon: str) -> None:
        self._install.disabled = not enabled
        self._install.icon = icon
        self._install.content = text(label, color=palette().on_accent)

    def show_error(self, message: str) -> None:
        self._error.value = message
        self.window.update()

    async def _check(self) -> None:
        self._set_busy(True)
        self._status.value = "Checking for updates"
        self._detail.value = "Asking Google for the latest release."
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
        self._progress_text.value = "Starting the download"
        self.window.update()

        def on_progress(progress: Progress) -> None:
            if progress.total:
                self._progress.value = progress.done / progress.total
                self._progress_text.value = (
                    f"Downloading {progress.done / 1_000_000:.1f} of {progress.total / 1_000_000:.1f} MB"
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
            self.window.notify("Platform-tools updated.")

    def _set_busy(self, busy: bool) -> None:
        self._check.disabled = busy
        self._install.disabled = busy


def _tool_row(name: str, version: ft.Text) -> ft.Container:
    colors = palette()
    location = managed_binary(name).parent
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=16),
        content=ft.Row(
            [
                ft.Column(
                    [
                        text(name, size=15, font=FONT_SEMIBOLD),
                        text(str(location), size=12, mono=True, color=colors.muted),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
                version,
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _version_text(version: Version | None) -> str:
    return str(version) if version else "Not installed"
