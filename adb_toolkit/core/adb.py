"""Thin wrapper around the adb command line."""

from adb_toolkit.core.devices import Device, parse_adb_devices
from adb_toolkit.core.packages import AppEntry, build_entries, parse_package_list
from adb_toolkit.core.platform_tools import find_tool
from adb_toolkit.core.process import CommandResult, run


class AdbError(RuntimeError):
    """A command adb needed to answer did not succeed."""


class Adb:
    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable

    @property
    def executable(self) -> str:
        # Resolved on every call, so a tool installed or updated later is picked up.
        return self._executable or find_tool("adb")

    def _run(self, *args: str, timeout: float = 30) -> CommandResult:
        return run([self.executable, *args], timeout=timeout)

    def devices(self) -> list[Device]:
        result = self._run("devices", "-l", timeout=10)
        return parse_adb_devices(result.stdout) if result.ok else []

    def connect(self, address: str) -> CommandResult:
        return self._run("connect", address, timeout=15)

    def reboot(self, serial: str, target: str | None = None) -> CommandResult:
        """Reboot to Android (target None), 'recovery' or 'bootloader'."""
        args = ["-s", serial, "reboot"]
        if target:
            args.append(target)
        return self._run(*args)

    def list_packages(self, serial: str) -> list[AppEntry]:
        installed = self._run("-s", serial, "shell", "pm", "list", "packages", timeout=60)
        system = self._run("-s", serial, "shell", "pm", "list", "packages", "-s", "-u", timeout=60)
        if not installed.ok:
            raise AdbError(installed.output or "Could not list packages.")
        if not system.ok:
            raise AdbError(system.output or "Could not list system packages.")
        return build_entries(parse_package_list(installed.stdout), parse_package_list(system.stdout))

    def uninstall(self, serial: str, package: str, *, system: bool) -> CommandResult:
        """User apps are removed. System apps are removed for user 0 and keep their data."""
        args = ["-s", serial, "shell", "pm", "uninstall"]
        if system:
            args.append("-k")
        args += ["--user", "0", package]
        return self._run(*args, timeout=60)

    def restore(self, serial: str, package: str) -> CommandResult:
        """Bring back a system app that was removed for user 0."""
        return self._run(
            "-s", serial, "shell", "cmd", "package", "install-existing", "--user", "0", package, timeout=60
        )

    def kill_server(self) -> CommandResult:
        return self._run("kill-server", timeout=10)
