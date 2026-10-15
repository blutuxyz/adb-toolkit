"""ADB Tools screen: commands that run through adb while the phone is booted into Android."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.adb import sideload_succeeded
from adb_toolkit.core.devices import ADB
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import SPACE_M, TYPE_CAPTION, palette
from adb_toolkit.ui.views.mirror import MirrorPanel
from adb_toolkit.ui.views.reboot import RebootTarget, RebootView
from adb_toolkit.ui.widgets import ONE_LINE, ProgressLine, button, card, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_TARGETS = (
    RebootTarget(
        None,
        "Reboot system",
        "Restart into Android.",
        "Rebooting the phone.",
        ft.Icons.RESTART_ALT,
        "green",
    ),
    RebootTarget(
        "recovery",
        "Reboot to recovery",
        "Sideload an update or factory reset.",
        "Rebooting to recovery.",
        ft.Icons.BUILD_CIRCLE_OUTLINED,
        "amber",
    ),
    RebootTarget(
        "bootloader",
        "Reboot to bootloader",
        "Switch to fastboot mode.",
        "Rebooting to the bootloader.",
        ft.Icons.FLASH_ON,
        "violet",
    ),
)


class AdbToolsView(RebootView):
    def __init__(self, window: Window) -> None:
        super().__init__(
            window,
            title=t("ADB Tools"),
            subtitle=t("Commands for a phone booted into Android."),
            icon=ft.Icons.TERMINAL,
            hue="green",
            targets=_TARGETS,
            accepts=lambda device: device.mode == ADB and device.is_ready,
            not_accepted_hint=lambda device: (
                t("The phone is in fastboot mode. Use Fastboot Tools instead.")
                if device.mode != ADB
                else t("The phone is {state}.", state=device.state)
            ),
            send=lambda serial, target: window.session.adb.reboot(serial, target),
        )
        self.mirror = MirrorPanel(window, self)
        self.sideload = SideloadCard(window)
        self.add_section(
            card(
                t("Screen mirroring"),
                [self.mirror.control],
                description=t("Show the phone's screen in a window on this computer."),
                icon=ft.Icons.SCREEN_SHARE,
                hue="green",
            )
        )
        self.add_section(self.sideload.control)

    async def activate(self) -> None:
        await super().activate()
        self.mirror.refresh()
        self.sideload.refresh()


class SideloadCard:
    """Installs a ROM or update ZIP. It works only while the phone is in recovery's sideload mode."""

    def __init__(self, window: Window) -> None:
        self.window = window
        colors = palette()
        self._zip: str | None = None
        self._name = text("", size=TYPE_CAPTION, mono=True, color=colors.muted, **ONE_LINE)
        self._progress = ProgressLine()
        self._choose = button(
            "outlined", t("Choose ZIP"), icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.window.page.run_task(self._pick),
        )
        self._start = button(
            "filled", t("Sideload"), icon=ft.Icons.SYSTEM_UPDATE_ALT,
            on_click=lambda _: self.window.page.run_task(self._sideload),
        )
        self._hint = text("", color=colors.muted)
        self.control = card(
            t("Sideload a ROM or update"),
            [
                ft.Row(
                    [self._choose, ft.Container(expand=True, content=self._name)],
                    spacing=SPACE_M,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self._start,
                self._progress.control,
                self._hint,
            ],
            description=t("Installs a ZIP through recovery. Choose Apply update from ADB on the phone first."),
            icon=ft.Icons.SYSTEM_UPDATE_ALT,
            hue="amber",
        )

    def refresh(self) -> None:
        device = self.window.session.selected_device
        ready = device is not None and device.mode == ADB and device.state == "sideload"
        busy = self.window.busy
        self._start.disabled = not ready or busy or self._zip is None
        self._choose.disabled = busy
        self._name.value = Path(self._zip).name if self._zip else t("No file chosen")
        self._hint.value = "" if ready else t("Start sideload on the phone first, from its recovery menu.")
        self.window.update()

    async def _pick(self) -> None:
        chosen = await self.window.pick_files(title=t("Choose a ROM or update"), extensions=["zip"])
        if chosen:
            self._zip = chosen[0]
        self.refresh()

    async def _sideload(self) -> None:
        device = self.window.session.selected_device
        if device is None or self._zip is None:
            return
        name = Path(self._zip).name
        self._progress.start(t("Sideloading {name}", name=name))
        self.refresh()
        try:
            result = await self.window.run_job(
                self.window.session.adb.sideload, device.serial, self._zip,
                on_line=self._progress.feed, on_tick=self._progress.tick,
            )
        finally:
            self._progress.hide()
            self.refresh()
        if sideload_succeeded(result.output):
            self.window.notify(t("Sideloaded {name}", name=name), success=True)
        else:
            self.window.notify(result.output or t("The sideload did not finish."), error=True)
