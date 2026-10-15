"""The command console: runs a typed adb or fastboot command, within limits.

It covers the commands the screens do not. It is a guard against accidents, not a sandbox:
commands that flash, erase, unlock, install, sideload or never finish are refused with a
pointer to the screen that does them safely. Nothing is passed to a shell.
"""

import shlex

from adb_toolkit.core.process import CommandResult, run

TOOLS = ("adb", "fastboot")
# Options the console must not take from the user, because it picks the phone itself.
_SERIAL_OPTIONS = ("-s", "-t", "-H", "-P")
# Commands that take no phone. Everything else gets the selected serial added.
_ADB_WITHOUT_SERIAL = {"devices", "connect", "disconnect", "kill-server", "start-server", "version", "help", "pair", "mdns"}
_FASTBOOT_WITHOUT_SERIAL = {"devices", "help", "--version", "-h"}
TIMEOUT = 120

_ADB_REFUSED = {
    "uninstall": "Use the Apps screen to uninstall an app.",
    "install": "Use the Files screen to install an APK.",
    "push": "Use the Files screen to send files to the phone.",
    "pull": "Use the Files screen to get files from the phone.",
    "sideload": "Use ADB Tools to sideload a ZIP.",
    "root": "Not run from the console.",
    "unroot": "Not run from the console.",
    "remount": "Not run from the console.",
    "disable-verity": "Not run from the console.",
    "enable-verity": "Not run from the console.",
}
_FASTBOOT_REFUSED = {
    "flash", "flashall", "erase", "format", "update", "set_active", "snapshot-update",
    "delete-logical-partition", "create-logical-partition", "resize-logical-partition",
    "oem", "flashing",
}
_FASTBOOT_REFUSED_MESSAGE = "Flashing, erasing and unlocking run from Fastboot Tools, where they ask for confirmation."


class ConsoleError(ValueError):
    """A line the console will not run. The message says what to do instead."""


def split(line: str) -> list[str]:
    """Split a typed line into words. Quotes group words, and backslashes in paths are kept."""
    try:
        tokens = shlex.split(line, posix=False)
    except ValueError as error:
        raise ConsoleError("A quote is not closed.") from error
    return [_unquote(token) for token in tokens]


def build(line: str, serial: str | None) -> tuple[str, list[str]]:
    """The tool and its arguments for a typed line, with the selected serial added where it applies.

    Raises ConsoleError for a line that must not run.
    """
    tokens = split(line)
    if not tokens:
        raise ConsoleError("Type a command, such as adb devices.")
    tool = tokens[0].lower().removesuffix(".exe")
    if tool not in TOOLS:
        raise ConsoleError("Only adb and fastboot commands run here.")

    args = tokens[1:]
    index = 0
    while index < len(args) and args[index].startswith("-"):
        if args[index][:2] in _SERIAL_OPTIONS:
            raise ConsoleError("Leave out -s, -t, -H and -P. The console uses the selected phone.")
        index += 1
    rest = args[index:]
    if not rest:
        raise ConsoleError(f"Add a command after {tool}, such as {tool} devices.")

    subcommand = rest[0].lower()
    if tool == "adb":
        _check_adb(subcommand, rest)
        needs_serial = subcommand not in _ADB_WITHOUT_SERIAL
    else:
        _check_fastboot(subcommand)
        needs_serial = subcommand not in _FASTBOOT_WITHOUT_SERIAL

    if serial and needs_serial:
        return tool, [*args[:index], "-s", serial, *rest]
    return tool, [*args[:index], *rest]


def run_line(line: str, serial: str | None, *, adb: str, fastboot: str) -> CommandResult:
    """Run a typed line with the given adb and fastboot programs. Raises ConsoleError if it must not run."""
    tool, args = build(line, serial)
    executable = adb if tool == "adb" else fastboot
    return run([executable, *args], timeout=TIMEOUT)


def _check_adb(subcommand: str, rest: list[str]) -> None:
    if subcommand in _ADB_REFUSED:
        raise ConsoleError(_ADB_REFUSED[subcommand])
    if subcommand.startswith("wait-for"):
        raise ConsoleError("That waits for the phone. Connect it first, then run the command again.")
    if subcommand == "logcat" and "-d" not in rest:
        raise ConsoleError("logcat keeps running until it is stopped. Add -d to print the log and stop.")
    if subcommand == "shell":
        payload = rest[1:]
        if not payload:
            raise ConsoleError("adb shell with no command waits for input. Add a command, such as adb shell getprop.")
        first = payload[0].lower()
        if first == "screenrecord":
            raise ConsoleError("Use the Capture screen to record the screen.")
        # top runs until stopped unless it is given -n; getevent only stops early with -p (print the devices and exit).
        if (first == "top" and "-n" not in payload) or (first == "getevent" and "-p" not in payload):
            raise ConsoleError(f"{first} keeps running until it is stopped. Give it a limit, or leave it out.")
        if first == "logcat" and "-d" not in payload:
            raise ConsoleError("logcat keeps running until it is stopped. Add -d to print the log and stop.")


def _check_fastboot(subcommand: str) -> None:
    if subcommand in _FASTBOOT_REFUSED:
        raise ConsoleError(_FASTBOOT_REFUSED_MESSAGE)


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token
