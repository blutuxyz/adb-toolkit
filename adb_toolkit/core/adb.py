"""Thin wrapper around the adb command line."""

from adb_toolkit.core.devices import Device, parse_adb_devices
from adb_toolkit.core.packages import AppEntry, build_entries, parse_package_list
from adb_toolkit.core.platform_tools import find_tool
from collections.abc import Callable

from adb_toolkit.core.process import CommandResult, run, stream

# Where screenshots and recordings are written on the phone before they are pulled to the PC.
PHONE_SCREENSHOT = "/sdcard/adb-toolkit-screenshot.png"
PHONE_RECORDING = "/sdcard/adb-toolkit-recording.mp4"
# The phone stops a recording at this length, whatever is asked for.
MAX_RECORDING_SECONDS = 180

LineHandler = Callable[[str], None]


class AdbError(RuntimeError):
    """A command adb needed to answer did not succeed."""


def install_succeeded(output: str) -> bool:
    return "Success" in output


def sideload_succeeded(output: str) -> bool:
    """adb prints a transfer total when a sideload completes. It can exit non-zero after a good transfer."""
    return "Total xfer" in output


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

    # Long commands: no time limit, and each output line goes to on_line as it arrives.

    def _stream(self, *args: str, on_line: LineHandler | None = None) -> CommandResult:
        return stream([self.executable, *args], on_line or (lambda _line: None))

    def install_apk(self, serial: str, apk: str, on_line: LineHandler | None = None) -> CommandResult:
        """Install an APK over the app that is there, keeping its data (-r)."""
        return self._stream("-s", serial, "install", "-r", apk, on_line=on_line)

    def push(self, serial: str, local: str, remote: str, on_line: LineHandler | None = None) -> CommandResult:
        return self._stream("-s", serial, "push", local, remote, on_line=on_line)

    def pull(self, serial: str, remote: str, local: str, on_line: LineHandler | None = None) -> CommandResult:
        return self._stream("-s", serial, "pull", remote, local, on_line=on_line)

    def sideload(self, serial: str, package: str, on_line: LineHandler | None = None) -> CommandResult:
        """Send a ROM or update ZIP to a phone in recovery's 'Apply update from ADB' mode."""
        return self._stream("-s", serial, "sideload", package, on_line=on_line)

    def screenshot(self, serial: str, local: str) -> CommandResult:
        """Save what the screen shows as a PNG. The copy on the phone is deleted afterwards."""
        self._run("-s", serial, "shell", "screencap", "-p", PHONE_SCREENSHOT, timeout=30)
        pulled = self.pull(serial, PHONE_SCREENSHOT, local)
        self._run("-s", serial, "shell", "rm", "-f", PHONE_SCREENSHOT, timeout=15)
        return pulled

    def record(self, serial: str, local: str, seconds: int, on_line: LineHandler | None = None) -> CommandResult:
        """Record the screen for a number of seconds, then pull the MP4. The copy on the phone is deleted."""
        seconds = max(1, min(int(seconds), MAX_RECORDING_SECONDS))
        self._stream(
            "-s", serial, "shell", "screenrecord", "--time-limit", str(seconds), PHONE_RECORDING, on_line=on_line
        )
        pulled = self.pull(serial, PHONE_RECORDING, local)
        self._run("-s", serial, "shell", "rm", "-f", PHONE_RECORDING, timeout=15)
        return pulled
