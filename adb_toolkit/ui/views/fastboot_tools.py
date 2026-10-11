"""Fastboot Tools screen: commands for a phone in bootloader (fastboot) mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import FASTBOOT
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
        "bootloader",
        "Reboot to bootloader",
        "Stay in fastboot mode.",
        "Rebooting to the bootloader.",
        ft.Icons.FLASH_ON,
        "violet",
    ),
    RebootTarget(
        "recovery",
        "Reboot to recovery",
        "Not every phone supports this.",
        "Rebooting to recovery.",
        ft.Icons.BUILD_CIRCLE_OUTLINED,
        "amber",
    ),
)


class FastbootToolsView(RebootView):
    def __init__(self, window: Window) -> None:
        super().__init__(
            window,
            title="Fastboot Tools",
            targets=_TARGETS,
            accepts=lambda device: device.mode == FASTBOOT,
            not_accepted_hint=lambda device: "Reboot to the bootloader from ADB Tools first.",
            send=lambda serial, target: window.session.fastboot.reboot(serial, target),
        )
