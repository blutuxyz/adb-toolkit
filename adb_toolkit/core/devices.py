"""Device model and the parsers for `adb devices -l` and `fastboot devices`."""

import re
from dataclasses import dataclass

ADB = "adb"
FASTBOOT = "fastboot"
READY_STATE = "device"

# Wi-Fi debugging serials look like 192.168.1.20:5555.
_NETWORK_SERIAL = re.compile(r"^[\w.-]+:\d{2,5}$")


@dataclass(frozen=True)
class Device:
    serial: str
    mode: str  # ADB or FASTBOOT
    state: str  # adb: device, unauthorized, offline, recovery, ...; fastboot: fastboot
    model: str = ""
    transport: str = ""  # "usb", "network", or "" when unknown

    @property
    def is_ready(self) -> bool:
        """True when adb can run commands on the device right now."""
        return self.mode == ADB and self.state == READY_STATE

    @property
    def title(self) -> str:
        return self.model or self.serial


def parse_adb_devices(output: str) -> list[Device]:
    devices = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("*", "List of devices")):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state, details = parts[0], parts[1], parts[2:]
        if state == "no" and details[:1] == ["permissions"]:
            state, details = "no permissions", details[1:]
        props = dict(part.split(":", 1) for part in details if ":" in part)
        devices.append(
            Device(
                serial=serial,
                mode=ADB,
                state=state,
                model=props.get("model", "").replace("_", " "),
                transport=_transport(serial, props),
            )
        )
    return devices


def parse_fastboot_devices(output: str) -> list[Device]:
    devices = []
    for raw_line in output.splitlines():
        parts = raw_line.split()
        if len(parts) == 2 and parts[1] == FASTBOOT:
            devices.append(Device(serial=parts[0], mode=FASTBOOT, state=FASTBOOT, transport="usb"))
    return devices


def _transport(serial: str, props: dict[str, str]) -> str:
    if "usb" in props:
        return "usb"
    if _NETWORK_SERIAL.match(serial):
        return "network"
    return ""
