"""Thin wrapper around the fastboot command line."""

import re

from adb_toolkit.core.devices import Device, parse_fastboot_devices
from adb_toolkit.core.platform_tools import find_tool
from adb_toolkit.core.process import CommandResult, run, stream

# "(bootloader) partition-size:boot_a: 0x4000000" is how getvar all names each partition.
_PARTITION = re.compile(r"partition-size:([^:\s]+):")


def parse_partitions(output: str) -> list[str]:
    """Partition names in the order fastboot lists them, without repeats."""
    names: list[str] = []
    for name in _PARTITION.findall(output):
        if name not in names:
            names.append(name)
    return names


class Fastboot:
    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable

    @property
    def executable(self) -> str:
        return self._executable or find_tool("fastboot")

    def _run(self, *args: str, timeout: float = 30) -> CommandResult:
        return run([self.executable, *args], timeout=timeout)

    def devices(self) -> list[Device]:
        result = self._run("devices", timeout=10)
        return parse_fastboot_devices(result.stdout) if result.ok else []

    def reboot(self, serial: str, target: str | None = None) -> CommandResult:
        """Reboot to Android (target None), 'bootloader' or 'recovery'."""
        args = ["-s", serial, "reboot"]
        if target:
            args.append(target)
        return self._run(*args)

    def getvar(self, serial: str, name: str) -> CommandResult:
        """Read one variable. fastboot writes the answer to stderr, so read `output`, not stdout."""
        return self._run("-s", serial, "getvar", name, timeout=15)

    def partitions(self, serial: str) -> list[str]:
        """Names of the partitions on the phone, read from `getvar all`. Empty if the query fails."""
        result = self._run("-s", serial, "getvar", "all", timeout=30)
        return parse_partitions(result.output) if result.ok else []

    def flash(self, serial: str, partition: str, image: str, on_line=None) -> CommandResult:
        """Write an image to a partition. This is destructive; the caller must confirm first."""
        return stream(
            [self.executable, "-s", serial, "flash", partition, image],
            on_line or (lambda _line: None),
        )
