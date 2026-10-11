"""First-run screen. It shows while platform-tools are downloaded, before the main window opens."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.platform_tools import Progress
from adb_toolkit.ui.theme import FONT_SEMIBOLD, palette
from adb_toolkit.ui.widgets import brand_mark, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_BODY = (
    "ADB Toolkit needs Google's adb and fastboot. They are downloaded from dl.google.com, "
    "checked against Google's SHA-1 checksum, and added to your user PATH."
)


class SetupView:
    def __init__(self, window: Window) -> None:
        self.window = window
        colors = palette()
        self._progress = ft.ProgressBar(value=None, color=colors.accent, bgcolor=colors.line)
        self._status = text("Checking the latest release", size=14, color=colors.muted)
        self._retry = ft.FilledButton(
            content=text("Try again", color=colors.on_accent),
            visible=False,
            on_click=lambda _: window.page.run_task(window.first_run),
        )
        self.control = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    brand_mark(52),
                    ft.Container(height=28),
                    text("Set up platform-tools", size=24, font=FONT_SEMIBOLD),
                    ft.Container(height=10),
                    text(_BODY, color=colors.muted),
                    ft.Container(height=32),
                    self._progress,
                    ft.Container(height=12),
                    self._status,
                    ft.Container(height=16),
                    self._retry,
                ],
                width=480,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def show_progress(self, progress: Progress) -> None:
        if progress.total:
            self._progress.value = progress.done / progress.total
            self._status.value = (
                f"Downloading {progress.done / 1_000_000:.1f} of {progress.total / 1_000_000:.1f} MB"
            )
        else:
            self._progress.value = None
            self._status.value = "Checking the latest release"

    def show_error(self, message: str) -> None:
        colors = palette()
        self._progress.value = 0
        self._status.value = message
        self._status.color = colors.danger
        self._retry.visible = True
        self.window.update()
