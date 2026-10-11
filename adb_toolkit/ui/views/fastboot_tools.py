"""Fastboot Tools screen: commands for a phone in bootloader (fastboot) mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

from adb_toolkit.core.devices import FASTBOOT
from adb_toolkit.ui.views.reboot import RebootTarget, RebootView

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_TARGETS = (
    RebootTarget(None, "Reboot system", "Restart the phone into Android.", "Rebooting the phone."),
    RebootTarget(
        "bootloader",
        "Reboot to bootloader",
        "Stay in fastboot mode. Use this before flashing a series of images.",
        "Rebooting to the bootloader.",
    ),
    RebootTarget(
        "recovery",
        "Reboot to recovery",
        "Start the recovery partition. Not every phone supports this from fastboot.",
        "Rebooting to recovery.",
    ),
)


class FastbootToolsView(RebootView):
    def __init__(self, window: Window) -> None:
        super().__init__(
            window,
            title="Fastboot Tools",
            subtitle="Commands for a phone in fastboot mode. Reboot it into fastboot from ADB Tools.",
            targets=_TARGETS,
            next_up="Coming next: flash firmware and the remaining fastboot operations.",
            accepts=lambda device: device.mode == FASTBOOT,
            not_accepted_hint=lambda device: (
                "The phone is booted into Android. Reboot it to the bootloader from ADB Tools first."
            ),
            send=lambda serial, target: window.session.fastboot.reboot(serial, target),
        )
