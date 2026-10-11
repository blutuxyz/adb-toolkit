from adb_toolkit.core.devices import ADB, FASTBOOT, Device, parse_adb_devices, parse_fastboot_devices

ADB_OUTPUT = """List of devices attached
R58M12ABCDE            device usb:1-1 product:b0qxxx model:SM_S911B device:dm3q transport_id:1
192.168.1.20:5555      device product:oriole model:Pixel_6 device:oriole transport_id:2
0123456789ABCDEF       unauthorized usb:2-2 transport_id:3
emulator-5554          offline
* daemon not running; starting now at tcp:5037
* daemon started successfully
"""


def test_parses_every_adb_device_with_its_state():
    devices = parse_adb_devices(ADB_OUTPUT)

    assert [device.serial for device in devices] == [
        "R58M12ABCDE",
        "192.168.1.20:5555",
        "0123456789ABCDEF",
        "emulator-5554",
    ]
    assert [device.state for device in devices] == ["device", "device", "unauthorized", "offline"]


def test_model_underscores_become_spaces_and_missing_model_falls_back_to_serial():
    devices = parse_adb_devices(ADB_OUTPUT)

    assert devices[0].model == "SM S911B"
    assert devices[0].title == "SM S911B"
    assert devices[3].title == "emulator-5554"


def test_transport_is_usb_for_cable_and_network_for_wifi_serials():
    usb, wifi, unauthorized, _ = parse_adb_devices(ADB_OUTPUT)

    assert usb.transport == "usb"
    assert wifi.transport == "network"
    assert unauthorized.transport == "usb"


def test_only_a_ready_adb_device_counts_as_ready():
    usb, wifi, unauthorized, offline = parse_adb_devices(ADB_OUTPUT)

    assert usb.is_ready and wifi.is_ready
    assert not unauthorized.is_ready
    assert not offline.is_ready


def test_linux_permission_problem_is_reported_as_its_own_state():
    output = "List of devices attached\nabc123 no permissions (user in plugdev group) usb:1-4 transport_id:9\n"

    (device,) = parse_adb_devices(output)

    assert device.serial == "abc123"
    assert device.state == "no permissions"
    assert device.transport == "usb"


def test_no_devices_gives_an_empty_list():
    assert parse_adb_devices("List of devices attached\n\n") == []


def test_parses_fastboot_devices_from_tab_separated_output():
    devices = parse_fastboot_devices("0123ABCD\tfastboot\n\nother-line here\n")

    assert devices == [Device(serial="0123ABCD", mode=FASTBOOT, state="fastboot", transport="usb")]


def test_fastboot_devices_are_not_ready_for_adb():
    (device,) = parse_fastboot_devices("0123ABCD\tfastboot\n")

    assert device.mode == FASTBOOT
    assert not device.is_ready
    assert device.mode != ADB
