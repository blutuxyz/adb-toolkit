"""Capture: a screenshot or a screen recording of the selected phone, saved to this computer."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.adb import MAX_RECORDING_SECONDS
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import SCROLL_PADDING, SECTION_GAP, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import ProgressLine, PillGroup, button, card, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

# The lengths offered for a recording. The phone never records longer than MAX_RECORDING_SECONDS.
_DURATIONS = ((10, "10 s"), (30, "30 s"), (MAX_RECORDING_SECONDS, "3 min"))


class CaptureView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._seconds = 30
        self._progress = ProgressLine()
        self._hint = text("", color=palette().muted)
        self._screenshot_button = button(
            "filled", t("Take screenshot"), icon=ft.Icons.PHOTO_CAMERA,
            on_click=lambda _: self.window.page.run_task(self._take_screenshot),
        )
        self._record_button = button(
            "filled", t("Start recording"), icon=ft.Icons.VIDEOCAM_OUTLINED,
            on_click=lambda _: self.window.page.run_task(self._record),
        )
        self._durations = PillGroup(
            tuple((str(seconds), t(label)) for seconds, label in _DURATIONS),
            str(self._seconds),
            self._on_duration,
        )

        self.body = ft.ListView(
            [
                card(
                    t("Screenshot"),
                    [self._screenshot_button],
                    description=t("Saves what the screen shows now, as a PNG."),
                    icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
                    hue="rose",
                ),
                card(
                    t("Screen recording"),
                    [
                        text(t("Length"), color=palette().muted),
                        self._durations.control,
                        self._record_button,
                        text(t("The phone stops a recording after 3 minutes at most."), color=palette().muted),
                    ],
                    description=t("Records the screen as an MP4 video, for the length you choose."),
                    icon=ft.Icons.VIDEOCAM_OUTLINED,
                    hue="rose",
                ),
                self._progress.control,
                ft.Container(content=self._hint),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(
            t("Capture"),
            self.body,
            subtitle=t("Save a screenshot or a recording of the selected phone's screen to this computer."),
            icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
            hue="rose",
        )

    async def activate(self) -> None:
        self._paint()

    def _paint(self) -> None:
        ready = self._ready()
        busy = self.window.busy
        self._screenshot_button.disabled = not ready or busy
        self._record_button.disabled = not ready or busy
        self._hint.value = "" if ready else t("Connect a phone with USB debugging on to use these.")
        self.window.update()

    def _on_duration(self, value: str) -> None:
        self._seconds = int(value)
        self._durations.select(value)

    async def _take_screenshot(self) -> None:
        serial = self._serial()
        if serial is None:
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = await self.window.pick_save_path(
            title=t("Save screenshot"), file_name=f"screenshot-{stamp}.png", extensions=["png"]
        )
        if not path:
            return
        self._progress.start(t("Taking screenshot"))
        self._paint()
        try:
            result = await self.window.run_job(
                self.window.session.adb.screenshot, serial, path, on_tick=self._progress.tick
            )
        finally:
            self._progress.hide()
            self._paint()
        if result.ok:
            self.window.notify(t("Saved {name}", name=path), success=True)
        else:
            self.window.notify(result.output or t("The screenshot did not finish."), error=True)

    async def _record(self) -> None:
        serial = self._serial()
        if serial is None:
            return
        seconds = self._seconds
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = await self.window.pick_save_path(
            title=t("Save recording"), file_name=f"recording-{stamp}.mp4", extensions=["mp4"]
        )
        if not path:
            return
        self._progress.start(t("Recording for {seconds} seconds", seconds=seconds))
        self._paint()
        try:
            result = await self.window.run_job(
                self.window.session.adb.record, serial, path, seconds,
                on_line=self._progress.feed, on_tick=self._progress.tick,
            )
        finally:
            self._progress.hide()
            self._paint()
        if result.ok:
            self.window.notify(t("Saved {name}", name=path), success=True)
        else:
            self.window.notify(result.output or t("The recording did not finish."), error=True)

    def _ready(self) -> bool:
        device = self.window.session.selected_device
        return device is not None and device.is_ready

    def _serial(self) -> str | None:
        device = self.window.session.selected_device
        return device.serial if device is not None and device.is_ready else None
