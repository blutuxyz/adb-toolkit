"""Run adb and fastboot without flashing console windows on Windows."""

import re
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import IO

# Progress as adb prints it: "[ 45%]" for push and pull, "(~45%)" for sideload.
_PERCENT = re.compile(r"(?:\[\s*|\(~?)(\d{1,3})%[\])]")


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        """stdout and stderr together, trimmed. Useful for showing a message."""
        return "\n".join(part for part in (self.stdout.strip(), self.stderr.strip()) if part)


def run(args: Sequence[str], *, timeout: float = 30) -> CommandResult:
    """Run a command and capture its output. Never raises for a failed command."""
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            **extra,
        )
    except OSError as error:
        return CommandResult(tuple(args), 127, "", f"{args[0]} could not be started: {error}")
    except subprocess.TimeoutExpired:
        return CommandResult(tuple(args), 124, "", f"{args[0]} timed out after {timeout:g} s")
    return CommandResult(tuple(args), completed.returncode, completed.stdout, completed.stderr)


def stream(args: Sequence[str], on_line: Callable[[str], None], *, timeout: float | None = None) -> CommandResult:
    """Run a long command and pass each line of its output to on_line as it arrives.

    Progress lines end with a carriage return rather than a newline, so both count as the end of a line.
    Stdin is closed, so a command that asks a question gets no answer and fails instead of hanging.
    The whole output is returned as well, so the caller can judge the result from it.
    """
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    try:
        process = subprocess.Popen(
            list(args),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            **extra,
        )
    except OSError as error:
        return CommandResult(tuple(args), 127, "", f"{args[0]} could not be started: {error}")
    # Reading blocks until the command ends, so the limit is a timer that kills the process.
    expired = threading.Event()

    def expire() -> None:
        expired.set()
        try:
            process.kill()
        except OSError:
            pass  # it finished on its own just now

    timer = threading.Timer(timeout, expire) if timeout is not None else None
    if timer is not None:
        timer.start()
    lines: list[str] = []
    try:
        for line in _lines(process.stdout):
            lines.append(line)
            on_line(line)
        code = process.wait()
    finally:
        if timer is not None:
            timer.cancel()
    if expired.is_set():
        return CommandResult(tuple(args), 124, "\n".join(lines), f"{args[0]} timed out")
    return CommandResult(tuple(args), code, "\n".join(lines))


def percent_of(line: str) -> int | None:
    """The progress a line reports, from 0 to 100, or None when the line has none."""
    match = _PERCENT.search(line)
    return min(int(match.group(1)), 100) if match else None


def _lines(stream_: IO[str]) -> Iterator[str]:
    """Split the text into lines on \\r or \\n. Blank pieces are skipped."""
    pending = ""
    while True:
        char = stream_.read(1)
        if not char:
            break
        if char in "\r\n":
            if pending.strip():
                yield pending
            pending = ""
        else:
            pending += char
    if pending.strip():
        yield pending
