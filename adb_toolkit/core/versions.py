"""Version numbers for platform-tools, such as 37.0.1."""

import re
from dataclasses import dataclass

_PLAIN_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# `adb version` prints "Version 37.0.1-13028021" on its own line, and
# `fastboot --version` prints "fastboot version 37.0.1-13028021".
_TOOL_VERSION = re.compile(
    r"^\s*(?:fastboot\s+)?version\s+(\d+)\.(\d+)\.(\d+)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    micro: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.micro}"

    @classmethod
    def parse(cls, text: str) -> "Version":
        match = _PLAIN_VERSION.match(text.strip())
        if match is None:
            raise ValueError(f"Not a version number: {text!r}")
        return cls(*(int(part) for part in match.groups()))


def parse_tool_version(output: str) -> Version | None:
    """Read the version from the output of `adb version` or `fastboot --version`."""
    match = _TOOL_VERSION.search(output)
    if match is None:
        return None
    return Version(*(int(part) for part in match.groups()))


def needs_update(installed: Version | None, latest: Version) -> bool:
    """True when the installed copy is missing or older than the latest release."""
    return installed is None or latest > installed
