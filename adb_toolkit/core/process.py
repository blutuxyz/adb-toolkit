"""Run adb and fastboot without flashing console windows on Windows."""

import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass


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
