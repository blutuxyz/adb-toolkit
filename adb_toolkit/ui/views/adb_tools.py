"""ADB Tools screen: commands that run through adb while the phone is booted into Android."""

from __future__ import annotations

from typing import TYPE_CHECKING

from adb_toolkit.core.devices import ADB
from adb_toolkit.ui.views.reboot import RebootTarget, RebootView

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_TARGETS = (
    RebootTarget(None, "Reboot system", "Restart the phone into Android.", "Rebooting the phone."),
    RebootTarget(
        "recovery",
        "Reboot to recovery",
        "Start the recovery partition, for sideloading an update or a factory reset.",
        "Rebooting to recovery.",
    ),
    RebootTarget(
        "bootloader",
        "Reboot to bootloader",
        "Switch to fastboot mode, for flashing images.",
        "Rebooting to the bootloader.",
    ),
)


class AdbToolsView(RebootView):
    def __init__(self, window: Window) -> None:
        super().__init__(
            window,
            title="ADB Tools",
            subtitle="Commands for a phone that is booted into Android with USB debugging on.",
            targets=_TARGETS,
            next_up="Coming next: install APK, sideload ROM, send file, custom command, screen mirroring.",
            accepts=lambda device: device.mode == ADB and device.is_ready,
            not_accepted_hint=lambda device: (
                "The phone is in fastboot mode. Use Fastboot Tools instead."
                if device.mode != ADB
                else f"The phone reports '{device.state}'. Commands start once it is ready."
            ),
            send=lambda serial, target: window.session.adb.reboot(serial, target),
        )
