"""Full-window download screen. It shows while platform-tools or scrcpy are downloaded and installed."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.platform_tools import Progress
from adb_toolkit.ui.theme import (
    FONT_SEMIBOLD,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XL,
    SPACE_XXL,
    TYPE_DISPLAY,
    palette,
)
from adb_toolkit.ui.widgets import brand_mark, button, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_CHECKING = "Checking the latest release"
_WIDTH = 480  # the setup column is narrower than the window, so the progress bar reads as a single track


class SetupView:
    """A progress screen. Once a download has failed it offers 'Try again' and, if `skip` is given, a way out."""

    def __init__(
        self,
        window: Window,
        *,
        title: str,
        body: str,
        retry: Callable[[], None],
        skip: Callable[[], None] | None = None,
        skip_label: str = "Continue",
    ) -> None:
        self.window = window
        colors = palette()
        self._progress = ft.ProgressBar(value=None, color=colors.accent, bgcolor=colors.line)
        self._status = text(_CHECKING, color=colors.muted)
        self._retry = button("filled", "Try again", on_click=lambda _: retry())
        self._skip = button(
            "outlined",
            skip_label,
            visible=skip is not None,
            on_click=lambda _: skip and skip(),
        )
        self._actions = ft.Row([self._retry, self._skip], spacing=SPACE_M, visible=False)
        self.control = ft.Container(
            expand=True,
            bgcolor=colors.background,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    brand_mark(56),
                    ft.Container(height=SPACE_XL),
                    text(title, size=TYPE_DISPLAY, font=FONT_SEMIBOLD),
                    ft.Container(height=SPACE_S),
                    text(body, color=colors.muted),
                    ft.Container(height=SPACE_XXL),
                    self._progress,
                    ft.Container(height=SPACE_M),
                    self._status,
                    ft.Container(height=SPACE_L),
                    self._actions,
                ],
                width=_WIDTH,
                spacing=0,
                tight=True,  # otherwise the column fills the height and the content sits at the top
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def show_progress(self, progress: Progress) -> None:
        if progress.total and progress.done >= progress.total:
            self._progress.value = None
            self._status.value = "Installing"
        elif progress.total:
            self._progress.value = progress.done / progress.total
            self._status.value = (
                f"Downloading {progress.done / 1_000_000:.1f} of {progress.total / 1_000_000:.1f} MB"
            )
        else:
            self._progress.value = None
            self._status.value = _CHECKING

    def show_error(self, message: str) -> None:
        colors = palette()
        self._progress.value = 0
        self._status.value = message
        self._status.color = colors.danger
        self._actions.visible = True
        self.window.update()

    def reset(self) -> None:
        """Back to the waiting state, for another attempt."""
        self._progress.value = None
        self._status.value = _CHECKING
        self._status.color = palette().muted
        self._actions.visible = False
        self.window.update()
