"""The screen section of ADB Tools: start and stop a scrcpy window, and choose how it looks."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import SCRCPY_RELEASES_URL
from adb_toolkit.core import paths
from adb_toolkit.core.scrcpy import MirrorOptions, ScrcpyError
from adb_toolkit.ui.theme import FONT_SEMIBOLD, palette
from adb_toolkit.ui.widgets import action_row, hairline, text

if TYPE_CHECKING:
    from adb_toolkit.ui.views.base import View
    from adb_toolkit.ui.window import Window

# "0" keeps the phone's own resolution.
_SIZES = (("0", "Original"), ("1440", "1440 px"), ("1080", "1080 px"), ("720", "720 px"))


class MirrorPanel:
    def __init__(self, window: Window, owner: View) -> None:
        self.window = window
        self._owner = owner
        self._options = MirrorOptions()
        self._stopping: str | None = None
        colors = palette()

        # Named after the methods they call, so no attribute hides a handler.
        self._start_button = ft.FilledButton(
            content=text("Start"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=lambda _: self.window.page.run_task(self._start_mirror),
        )
        self._stop_button = ft.OutlinedButton(
            content=text("Stop"),
            icon=ft.Icons.STOP,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self._stop_mirror),
        )
        self._get_button = ft.OutlinedButton(
            content=text("Get scrcpy"),
            icon=ft.Icons.OPEN_IN_NEW,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self.window.open_url, SCRCPY_RELEASES_URL),
        )
        self._status = text("", size=13, color=colors.muted)
        self._stay_awake = ft.Switch(
            label="Keep the phone awake",
            value=self._options.stay_awake,
            active_color=colors.accent,
            on_change=self._on_switch("stay_awake"),
        )
        self._screen_off = ft.Switch(
            label="Turn off the phone's screen",
            value=self._options.screen_off,
            active_color=colors.accent,
            on_change=self._on_switch("screen_off"),
        )
        self._show_touches = ft.Switch(
            label="Show touches",
            value=self._options.show_touches,
            active_color=colors.accent,
            on_change=self._on_switch("show_touches"),
        )
        self._size = ft.Dropdown(
            options=[ft.DropdownOption(key=key, text=label) for key, label in _SIZES],
            value="0",
            width=160,
            on_select=self._on_size,
        )

        self.control = ft.Column(
            [
                text("Screen", size=18, font=FONT_SEMIBOLD),
                ft.Container(height=4),
                action_row(
                    "Mirror and control",
                    "Mouse and keyboard control the phone from its window.",
                    ft.Row([self._stop_button, self._start_button], spacing=12),
                    icon=ft.Icons.SCREEN_SHARE,
                    hue="blue",
                ),
                hairline(),
                ft.Container(
                    padding=ft.Padding.only(left=56, top=12, bottom=4),
                    content=ft.Column([self._stay_awake, self._screen_off, self._show_touches], spacing=4),
                ),
                ft.Container(
                    padding=ft.Padding.only(left=56, top=8, bottom=8),
                    content=ft.Row(
                        [text("Maximum size", size=14), ft.Container(expand=True), self._size],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Row(
                    [ft.Container(expand=True, content=self._status), self._get_button],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        )

    def refresh(self) -> None:
        """Redraw the buttons and the status line for the selected phone."""
        session = self.window.session
        colors = palette()
        device = session.selected_device
        installed = session.scrcpy.find() is not None
        ready = device is not None and device.is_ready
        running = ready and session.scrcpy.running(device.serial)

        self._start_button.disabled = not (ready and installed and not running)
        self._stop_button.visible = running
        self._get_button.visible = not installed
        self._status.color = colors.muted
        if not installed:
            self._status.value = f"scrcpy is not installed. Put it in {paths.scrcpy_dir()} or on PATH."
            self._status.color = colors.signal
        elif device is None:
            self._status.value = "Connect a phone to mirror it."
        elif not ready:
            self._status.value = "The phone must be ready before it can be mirrored."
        elif running:
            self._status.value = f"Mirroring {device.title}."
            self._status.color = colors.accent
        else:
            self._status.value = ""
        self.window.update()

    async def _start_mirror(self) -> None:
        session = self.window.session
        device = session.selected_device
        if device is None or not device.is_ready:
            self.window.notify("Select a ready phone first.", error=True)
            return
        try:
            process = session.scrcpy.start(device.serial, self._options, session.adb.executable)
        except ScrcpyError as error:
            self.window.notify(str(error), error=True)
            self.refresh()
            return
        asyncio.ensure_future(self._watch(device.serial, process))
        self.refresh()

    async def _stop_mirror(self) -> None:
        device = self.window.session.selected_device
        if device is None:
            return
        self._stopping = device.serial
        await asyncio.to_thread(self.window.session.scrcpy.stop, device.serial)
        self.refresh()

    async def _watch(self, serial: str, process) -> None:
        """Wait for the window to close, then say so if it did not close on purpose."""
        code = await asyncio.to_thread(process.wait)
        if self._stopping == serial:
            self._stopping = None
        elif code != 0:
            detail = self.window.session.scrcpy.log_tail()
            self.window.notify(detail or "scrcpy closed.", error=True)
        if self._is_showing():
            self.refresh()

    def _is_showing(self) -> bool:
        shell = self.window.shell
        return shell is not None and shell.current == "adb" and shell.views.get("adb") is self._owner

    def _on_switch(self, field: str):
        def handle(event: ft.ControlEvent) -> None:
            self._options = replace(self._options, **{field: _is_on(event.data)})

        return handle

    def _on_size(self, event: ft.ControlEvent) -> None:
        value = event.data if isinstance(event.data, str) else event.control.value
        self._options = replace(self._options, max_size=int(value or "0") or None)


def _is_on(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"
