"""The screen section of ADB Tools: start and stop a scrcpy window, and choose how it looks."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.scrcpy import MirrorOptions, ScrcpyError
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import CONTROL_HEIGHT, RADIUS_CONTROL, SPACE_M, SPACE_S, palette
from adb_toolkit.ui.widgets import button, hairline, row_item, text

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
        self._start_button = button(
            "filled",
            t("Start"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=lambda _: self.window.page.run_task(self._start_mirror),
        )
        self._stop_button = button(
            "outlined",
            t("Stop"),
            icon=ft.Icons.STOP,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self._stop_mirror),
        )
        self._install_button = button(
            "outlined",
            t("Install scrcpy"),
            icon=ft.Icons.DOWNLOAD,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self.window.update_scrcpy),
        )
        self._status = text("", color=colors.muted, strong=True)
        self._stay_awake = _switch(self._options.stay_awake, self._on_switch("stay_awake"))
        self._screen_off = _switch(self._options.screen_off, self._on_switch("screen_off"))
        self._show_touches = _switch(self._options.show_touches, self._on_switch("show_touches"))
        self._size = ft.Dropdown(
            options=[ft.DropdownOption(key=key, text=t(label)) for key, label in _SIZES],
            value="0",
            width=160,
            height=CONTROL_HEIGHT,
            border_radius=RADIUS_CONTROL,
            border_color=colors.control_border,
            focused_border_color=colors.accent,
            on_select=self._on_size,
        )

        self.control = ft.Column(
            [
                row_item(
                    t("Mirror and control"),
                    t("Mouse and keyboard control the phone from its window."),
                    ft.Row([self._stop_button, self._start_button], spacing=SPACE_M),
                ),
                hairline(),
                row_item(
                    t("Keep the phone awake"),
                    t("Stops the phone from sleeping while it is mirrored."),
                    self._stay_awake,
                ),
                hairline(),
                row_item(
                    t("Turn off the phone's screen"),
                    t("The phone's own screen stays dark while you use the window."),
                    self._screen_off,
                ),
                hairline(),
                row_item(
                    t("Show touches"),
                    t("Draws a dot where each touch lands."),
                    self._show_touches,
                ),
                hairline(),
                row_item(
                    t("Maximum size"),
                    t("Scales the window down. Original keeps the phone's resolution."),
                    self._size,
                ),
                ft.Container(
                    padding=ft.Padding.only(top=SPACE_S),
                    content=ft.Row(
                        [ft.Container(expand=True, content=self._status), self._install_button],
                        spacing=SPACE_M,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            spacing=0,
            tight=True,
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
        self._install_button.visible = not installed
        self._status.color = colors.muted
        if not installed:
            self._status.value = t("scrcpy is not installed.")
            self._status.color = colors.signal
        elif device is None:
            self._status.value = t("Connect a phone to mirror it.")
        elif not ready:
            self._status.value = t("The phone must be ready before it can be mirrored.")
        elif running:
            self._status.value = t("Mirroring {title}.", title=device.title)
            self._status.color = colors.accent
        else:
            self._status.value = ""
        self.window.update()

    async def _start_mirror(self) -> None:
        session = self.window.session
        device = session.selected_device
        if device is None or not device.is_ready:
            self.window.notify(t("Select a ready phone first."), error=True)
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
            self.window.notify(detail or t("scrcpy closed."), error=True)
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


def _switch(value: bool, on_change) -> ft.Switch:
    return ft.Switch(value=value, active_color=palette().accent, on_change=on_change)


def _is_on(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"
