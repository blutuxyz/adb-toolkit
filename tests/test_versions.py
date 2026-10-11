import pytest

from adb_toolkit.core.versions import Version, needs_update, parse_tool_version

ADB_VERSION_OUTPUT = """Android Debug Bridge version 1.0.41
Version 37.0.1-13028021
Installed as C:\\Users\\me\\AppData\\Local\\ADB Toolkit\\platform-tools\\adb.exe
"""

FASTBOOT_VERSION_OUTPUT = """fastboot version 37.0.1-13028021
Installed as C:\\Users\\me\\AppData\\Local\\ADB Toolkit\\platform-tools\\fastboot.exe
"""


def test_reads_adb_version_and_ignores_the_protocol_version_line():
    assert parse_tool_version(ADB_VERSION_OUTPUT) == Version(37, 0, 1)


def test_reads_fastboot_version():
    assert parse_tool_version(FASTBOOT_VERSION_OUTPUT) == Version(37, 0, 1)


def test_returns_none_for_unrecognised_output():
    assert parse_tool_version("command not found") is None


def test_versions_compare_numerically_not_as_text():
    assert Version(37, 0, 1) > Version(36, 0, 0)
    assert Version(9, 0, 0) < Version(10, 0, 0)


def test_parse_accepts_plain_numbers_and_rejects_anything_else():
    assert Version.parse("37.0.1") == Version(37, 0, 1)
    with pytest.raises(ValueError):
        Version.parse("37.0")


def test_missing_install_needs_an_update():
    assert needs_update(None, Version(37, 0, 1)) is True


def test_same_version_is_up_to_date():
    assert needs_update(Version(37, 0, 1), Version(37, 0, 1)) is False


def test_older_install_needs_an_update():
    assert needs_update(Version(36, 0, 0), Version(37, 0, 1)) is True
