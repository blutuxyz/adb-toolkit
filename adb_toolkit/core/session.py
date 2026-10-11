"""What the app knows right now: attached devices, the selected one, tool versions and settings.

Holds no UI code, so the selection and update rules can be tested directly.
"""

import logging
from pathlib import Path

from adb_toolkit.core import paths, settings
from adb_toolkit.core.adb import Adb
from adb_toolkit.core.devices import ADB, READY_STATE, Device
from adb_toolkit.core.fastboot import Fastboot
from adb_toolkit.core.platform_tools import LocalInstall
from adb_toolkit.core.updates import RemotePlatformTools
from adb_toolkit.core.versions import Version, needs_update

log = logging.getLogger(__name__)


class Session:
    def __init__(
        self,
        adb: Adb | None = None,
        fastboot: Fastboot | None = None,
        settings_path: Path | None = None,
    ) -> None:
        self.adb = adb or Adb()
        self.fastboot = fastboot or Fastboot()
        self._settings_path = settings_path
        self.settings = settings.load(self.settings_path)
        self.local = LocalInstall(installed=False)
        self.remote: RemotePlatformTools | None = None
        self.devices: list[Device] = []
        self.selected_serial: str | None = None

    @property
    def settings_path(self) -> Path:
        return self._settings_path or paths.settings_file()

    @property
    def latest(self) -> Version | None:
        return self.remote.version if self.remote else None

    @property
    def update_available(self) -> bool:
        if self.remote is None or not self.local.installed:
            return False
        return needs_update(self.local.adb_version, self.remote.version)

    @property
    def selected_device(self) -> Device | None:
        return next((device for device in self.devices if device.serial == self.selected_serial), None)

    def scan(self) -> list[Device]:
        """Blocking. Asks adb and fastboot which devices are attached."""
        return self.adb.devices() + self.fastboot.devices()

    def update_devices(self, devices: list[Device]) -> bool:
        """Store a fresh device list and keep the selection valid. Returns True if the list changed."""
        changed = devices != self.devices
        self.devices = list(devices)
        if self.selected_serial not in {device.serial for device in self.devices}:
            self.selected_serial = _default_serial(self.devices)
        return changed

    def select(self, serial: str) -> None:
        if any(device.serial == serial for device in self.devices):
            self.selected_serial = serial

    def set_theme_mode(self, mode: str) -> None:
        self.settings.theme_mode = mode
        try:
            settings.save(self.settings_path, self.settings)
        except OSError as error:
            log.warning("Could not save settings: %s", error)


def _default_serial(devices: list[Device]) -> str | None:
    """Prefer a device adb can talk to, then whatever is first in the list."""
    for device in devices:
        if device.mode == ADB and device.state == READY_STATE:
            return device.serial
    return devices[0].serial if devices else None
