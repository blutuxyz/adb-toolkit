"""Console: type an adb or fastboot command and read what it prints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.console import ConsoleError, run_line
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    FONT_MONO,
    RADIUS_CARD,
    RADIUS_CONTROL,
    SPACE_L,
    SPACE_S,
    SPACE_XS,
    TYPE_BODY,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import PillGroup, button, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

HISTORY_SIZE = 8  # recent commands offered as pills
LOG_LINES = 400  # the log keeps this many lines, so a long session stays quick


class ConsoleView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._history: list[str] = []
        self._log_lines: list[ft.Control] = []
        self._input = ft.TextField(
            hint_text=t("adb devices"),
            expand=True,
            height=CONTROL_HEIGHT,
            border_radius=RADIUS_CONTROL,
            border_color=colors.control_border,
            focused_border_color=colors.accent,
            cursor_color=colors.accent,
            text_style=ft.TextStyle(font_family=FONT_MONO),
            on_submit=lambda _: self.window.page.run_task(self._run),
        )
        self._run_button = button(
            "filled", t("Run"), icon=ft.Icons.PLAY_ARROW,
            on_click=lambda _: self.window.page.run_task(self._run),
        )
        self._history_row = ft.Container()
        self._log = ft.ListView(expand=True, spacing=SPACE_XS, padding=SPACE_L, auto_scroll=True)
        self._log_surface = ft.Container(
            expand=True,
            bgcolor=colors.panel,
            border=ft.Border.all(1, colors.line),
            border_radius=RADIUS_CARD,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self._log,
        )
        self._hint = text(
            t("The console adds the selected phone. Flashing, unlocking, uninstalling and sideloading have their own screens."),
            size=TYPE_BODY,
            color=colors.muted,
        )

        self.control = screen_frame(
            t("Console"),
            ft.Column(
                [
                    ft.Row([self._input, self._run_button], spacing=SPACE_S,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self._history_row,
                    self._hint,
                    self._log_surface,
                ],
                spacing=SPACE_S,
                expand=True,
            ),
            subtitle=t("Run an adb or fastboot command, and read what it prints."),
            icon=ft.Icons.CODE,
            hue="blue",
        )

    async def activate(self) -> None:
        self.window.update()

    async def _run(self) -> None:
        line = (self._input.value or "").strip()
        if not line or self.window.busy:
            return
        self._input.value = ""
        self._remember(line)
        self._append(text(f"$ {line}", mono=True, strong=True, color=palette().accent))
        self._run_button.disabled = True
        self.window.update()

        device = self.window.session.selected_device
        serial = device.serial if device is not None else None
        session = self.window.session
        try:
            result = await self.window.run_job(
                run_line, line, serial, adb=session.adb.executable, fastboot=session.fastboot.executable
            )
        except ConsoleError as error:
            self._append(text(str(error), mono=True, color=palette().signal))
        else:
            output = result.output or t("(no output)")
            for part in output.splitlines():
                self._append(text(part, mono=True, color=palette().text))
            if not result.ok:
                self._append(text(t("Exit code {code}", code=result.returncode), mono=True, color=palette().danger))
        finally:
            self._run_button.disabled = False
            self._history_row.content = self._pills()
            self.window.update()

    def _remember(self, line: str) -> None:
        if line in self._history:
            self._history.remove(line)
        self._history.insert(0, line)
        del self._history[HISTORY_SIZE:]

    def _pills(self) -> ft.Control | None:
        if not self._history:
            return None
        group = PillGroup(tuple((line, line) for line in self._history), "", self._fill, scroll=True)
        return group.control

    def _fill(self, line: str) -> None:
        self._input.value = line
        self.window.update()

    def _append(self, control: ft.Control) -> None:
        self._log_lines.append(control)
        del self._log_lines[:-LOG_LINES]
        self._log.controls = list(self._log_lines)
        self.window.update()
