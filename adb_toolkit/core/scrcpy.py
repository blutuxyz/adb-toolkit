"""Mirror a phone on this computer and control it with scrcpy.

scrcpy is a separate program with its own releases, so the toolkit does not ship it.
`scrcpy_install.py` downloads it into the toolkit's own folder. It is looked for there
first, then on PATH. The toolkit starts one window per phone and keeps track of it.
scrcpy does the streaming and the input, and it talks to the phone through the adb
named in the ADB environment variable.
"""

import atexit
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from adb_toolkit.core import paths

log = logging.getLogger(__name__)

EXECUTABLE_NAME = "scrcpy.exe" if sys.platform == "win32" else "scrcpy"
STOP_TIMEOUT = 3  # seconds to wait for a window to close before it is killed


def managed_executable() -> Path:
    """Where the toolkit's own copy of scrcpy lives. It may not exist yet."""
    return paths.scrcpy_dir() / EXECUTABLE_NAME


class ScrcpyError(RuntimeError):
    """scrcpy is missing, or it could not be started."""


@dataclass(frozen=True)
class MirrorOptions:
    max_size: int | None = None  # None keeps the phone's own resolution
    stay_awake: bool = True
    screen_off: bool = False  # turn the phone's screen off while it is mirrored
    show_touches: bool = False


def build_args(executable: Path | str, serial: str, options: MirrorOptions, title: str) -> list[str]:
    args = [str(executable), "-s", serial, f"--window-title={title}"]
    if options.max_size:
        args.append(f"--max-size={options.max_size}")
    if options.stay_awake:
        args.append("--stay-awake")
    if options.screen_off:
        args.append("--turn-screen-off")
    if options.show_touches:
        args.append("--show-touches")
    return args


class Scrcpy:
    """Finds scrcpy and keeps one running window per phone."""

    def __init__(self, executable: Path | None = None, log_file: Path | None = None) -> None:
        self._executable = executable
        self._log_file = log_file
        self._processes: dict[str, subprocess.Popen] = {}
        atexit.register(self.stop_all)

    @property
    def log_file(self) -> Path:
        return self._log_file or paths.scrcpy_log()

    def find(self) -> Path | None:
        """The scrcpy program to run, or None when it is not installed."""
        if self._executable is not None:
            return self._executable if self._executable.is_file() else None
        managed = managed_executable()
        if managed.is_file():
            return managed
        found = shutil.which("scrcpy")
        return Path(found) if found else None

    def running(self, serial: str) -> bool:
        process = self._processes.get(serial)
        return process is not None and process.poll() is None

    def any_running(self) -> bool:
        return any(self.running(serial) for serial in self._processes)

    def start(self, serial: str, options: MirrorOptions, adb: str) -> subprocess.Popen:
        """Open a mirror window for the phone. Raises ScrcpyError if one is open already or scrcpy is missing."""
        if self.running(serial):
            raise ScrcpyError(f"{serial} is already being mirrored.")
        executable = self.find()
        if executable is None:
            raise ScrcpyError("scrcpy is not installed.")
        args = build_args(executable, serial, options, title=f"ADB Toolkit - {serial}")
        env = {**os.environ, "ADB": adb}
        extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        # scrcpy's own messages go to a log file, so a failed start can be explained.
        with self.log_file.open("w", encoding="utf-8") as output:
            try:
                process = subprocess.Popen(args, env=env, stdout=output, stderr=subprocess.STDOUT, **extra)
            except OSError as error:
                raise ScrcpyError(f"scrcpy could not be started: {error}") from error
        self._processes[serial] = process
        log.info("Started scrcpy for %s", serial)
        return process

    def stop(self, serial: str) -> None:
        process = self._processes.pop(serial, None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()

    def stop_all(self) -> None:
        for serial in list(self._processes):
            self.stop(serial)

    def log_tail(self, lines: int = 3) -> str:
        """The last few lines scrcpy printed. Empty if there is no log yet."""
        try:
            text = self.log_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        kept = [line for line in text.splitlines() if line.strip()]
        return "\n".join(kept[-lines:])
