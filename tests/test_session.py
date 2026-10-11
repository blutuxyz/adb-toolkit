from adb_toolkit.core.adb import Adb
from adb_toolkit.core.devices import Device
from adb_toolkit.core.fastboot import Fastboot
from adb_toolkit.core.platform_tools import LocalInstall
from adb_toolkit.core.session import Session
from adb_toolkit.core.updates import RemotePlatformTools
from adb_toolkit.core.versions import Version


def _session(tmp_path) -> Session:
    return Session(
        adb=Adb(executable="adb-not-used"),
        fastboot=Fastboot(executable="fastboot-not-used"),
        settings_path=tmp_path / "settings.json",
    )


def _ready(serial: str) -> Device:
    return Device(serial=serial, mode="adb", state="device", transport="usb")


def _unauthorized(serial: str) -> Device:
    return Device(serial=serial, mode="adb", state="unauthorized", transport="usb")


def test_first_ready_device_is_selected_by_default(tmp_path):
    session = _session(tmp_path)

    session.update_devices([_unauthorized("A"), _ready("B"), _ready("C")])

    assert session.selected_serial == "B"


def test_selection_is_kept_while_the_device_stays_attached(tmp_path):
    session = _session(tmp_path)
    session.update_devices([_ready("A"), _ready("B")])
    session.select("B")

    changed = session.update_devices([_ready("A"), _ready("B")])

    assert changed is False
    assert session.selected_serial == "B"


def test_selection_moves_when_the_selected_device_is_unplugged(tmp_path):
    session = _session(tmp_path)
    session.update_devices([_ready("A"), _ready("B")])
    session.select("B")

    session.update_devices([_ready("A")])

    assert session.selected_serial == "A"
    assert session.selected_device == _ready("A")


def test_no_devices_clears_the_selection(tmp_path):
    session = _session(tmp_path)
    session.update_devices([_ready("A")])

    session.update_devices([])

    assert session.selected_serial is None
    assert session.selected_device is None


def test_select_ignores_serials_that_are_not_attached(tmp_path):
    session = _session(tmp_path)
    session.update_devices([_ready("A")])

    session.select("ZZZ")

    assert session.selected_serial == "A"


def test_update_is_available_only_when_a_newer_release_exists(tmp_path):
    session = _session(tmp_path)
    session.local = LocalInstall(installed=True, adb_version=Version(36, 0, 0), fastboot_version=Version(36, 0, 0))
    session.remote = RemotePlatformTools(version=Version(37, 0, 1))

    assert session.update_available is True

    session.local = LocalInstall(installed=True, adb_version=Version(37, 0, 1), fastboot_version=Version(37, 0, 1))
    assert session.update_available is False


def test_nothing_is_offered_before_tools_are_installed(tmp_path):
    session = _session(tmp_path)
    session.remote = RemotePlatformTools(version=Version(37, 0, 1))

    assert session.update_available is False


def test_theme_choice_is_saved_and_read_back(tmp_path):
    session = _session(tmp_path)

    session.set_theme_mode("light")

    assert _session(tmp_path).settings.theme_mode == "light"
