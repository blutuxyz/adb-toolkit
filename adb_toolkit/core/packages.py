"""Build the app list from `pm list packages` output."""

from dataclasses import dataclass

PACKAGE_PREFIX = "package:"
SYSTEM = "system"
USER = "user"


@dataclass(frozen=True, order=True)
class AppEntry:
    package: str
    kind: str  # SYSTEM or USER
    installed: bool  # False for a system app that was removed for this user

    @property
    def removed(self) -> bool:
        return self.kind == SYSTEM and not self.installed

    @property
    def tag(self) -> str:
        if self.removed:
            return "Removed system app"
        return "System app" if self.kind == SYSTEM else "User app"


def parse_package_list(output: str) -> set[str]:
    """Package names from `pm list packages`, one per line as 'package:<name>'."""
    names = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith(PACKAGE_PREFIX):
            name = line[len(PACKAGE_PREFIX):].strip()
            if name:
                names.add(name)
    return names


def build_entries(installed: set[str], system: set[str]) -> list[AppEntry]:
    """Combine the installed packages with every system package, sorted by name.

    `system` must include system apps that were removed, which is what
    `pm list packages -s -u` returns. That is how a removed app stays visible.
    """
    entries = [
        AppEntry(package=name, kind=SYSTEM if name in system else USER, installed=name in installed)
        for name in installed | system
    ]
    return sorted(entries, key=lambda entry: entry.package)


def uninstall_succeeded(output: str) -> bool:
    return "Success" in output


def restore_succeeded(output: str) -> bool:
    lowered = output.lower()
    return "installed for user" in lowered or "already installed" in lowered
