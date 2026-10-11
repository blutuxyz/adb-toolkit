"""Thin wrapper around the fastboot command line."""

from adb_toolkit.core.devices import Device, parse_fastboot_devices
from adb_toolkit.core.platform_tools import find_tool
from adb_toolkit.core.process import CommandResult, run


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
