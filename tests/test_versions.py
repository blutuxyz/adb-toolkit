import pytest

from adb_toolkit.core.versions import (
    Version,
    needs_update,
    parse_release_tag,
    parse_scrcpy_version,
    parse_tool_version,
)

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


def test_scrcpy_prints_its_version_on_the_first_line():
    output = "scrcpy 3.3.3 <https://github.com/Genymobile/scrcpy>\n\n dependencies"
    assert parse_scrcpy_version(output) == Version(3, 3, 3)


def test_an_old_scrcpy_version_without_a_third_number_reads_as_zero():
    assert parse_scrcpy_version("scrcpy 2.0 <https://github.com/Genymobile/scrcpy>") == Version(2, 0, 0)


def test_other_output_is_not_a_scrcpy_version():
    assert parse_scrcpy_version("The system cannot find the file specified.") is None


def test_release_tags_may_carry_a_v_and_skip_the_third_number():
    assert parse_release_tag("v5.0.1") == Version(5, 0, 1)
    assert parse_release_tag("v2.0") == Version(2, 0, 0)
    assert parse_release_tag("nightly") is None
