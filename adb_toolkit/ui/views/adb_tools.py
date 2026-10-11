"""ADB Tools screen: commands that run through adb while the phone is booted into Android."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import ADB
from adb_toolkit.ui.theme import SECTION_GAP
from adb_toolkit.ui.views.mirror import MirrorPanel
from adb_toolkit.ui.views.reboot import RebootTarget, RebootView

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
            title="ADB Tools",
            targets=_TARGETS,
            accepts=lambda device: device.mode == ADB and device.is_ready,
            not_accepted_hint=lambda device: (
                "The phone is in fastboot mode. Use Fastboot Tools instead."
                if device.mode != ADB
                else f"The phone is {device.state}."
            ),
            send=lambda serial, target: window.session.adb.reboot(serial, target),
        )
        self.mirror = MirrorPanel(window, self)
        self.control.controls.extend([ft.Container(height=SECTION_GAP), self.mirror.control])

    async def activate(self) -> None:
        await super().activate()
        self.mirror.refresh()
