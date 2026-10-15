"""The console runs adb and fastboot commands, and refuses the ones that flash, erase, install or never finish."""

import pytest

from adb_toolkit.core import console
from adb_toolkit.core.console import ConsoleError, build, run_line, split


def test_a_plain_command_runs_as_typed():
    assert build("adb devices", None) == ("adb", ["devices"])


def test_the_selected_phone_is_added_to_device_commands():
    assert build("adb shell getprop ro.product.model", "R58") == (
        "adb", ["-s", "R58", "shell", "getprop", "ro.product.model"],
    )
    assert build("fastboot getvar all", "F1") == ("fastboot", ["-s", "F1", "getvar", "all"])


def test_commands_that_take_no_phone_get_no_serial():
    assert build("adb devices", "R58") == ("adb", ["devices"])
    assert build("fastboot devices", "F1") == ("fastboot", ["devices"])


def test_quotes_group_words_and_windows_paths_keep_their_backslashes():
    assert split('adb shell "echo hi there"') == ["adb", "shell", "echo hi there"]
    assert split(r"adb push C:\Temp\a.txt /sdcard/") == ["adb", "push", r"C:\Temp\a.txt", "/sdcard/"]


def test_the_tool_name_ignores_case_and_an_exe_suffix():
    assert build("ADB.exe devices", None) == ("adb", ["devices"])


@pytest.mark.parametrize("line", ["", "   ", "adb", "rm -rf /", "powershell Get-Process"])
def test_empty_lines_and_other_programs_are_refused(line):
    with pytest.raises(ConsoleError):
        build(line, "R58")


@pytest.mark.parametrize("line", ["adb -s other devices", "adb -t 1 devices", "adb -H host devices",
                                  "fastboot -s other getvar all"])
def test_the_user_cannot_pick_a_phone_themselves(line):
    with pytest.raises(ConsoleError, match="selected phone"):
        build(line, "R58")


@pytest.mark.parametrize("line, pointer", [
    ("adb uninstall com.example", "Apps"),
    ("adb install a.apk", "Files"),
    ("adb push a.txt /sdcard/", "Files"),
    ("adb pull /sdcard/a.txt .", "Files"),
    ("adb sideload rom.zip", "ADB Tools"),
    ("adb root", "console"),
    ("fastboot flash boot boot.img", "Fastboot Tools"),
    ("fastboot erase userdata", "Fastboot Tools"),
    ("fastboot format userdata", "Fastboot Tools"),
    ("fastboot oem unlock", "Fastboot Tools"),
    ("fastboot flashing unlock", "Fastboot Tools"),
])
def test_destructive_commands_point_to_the_screen_that_does_them(line, pointer):
    with pytest.raises(ConsoleError, match=pointer):
        build(line, None)


@pytest.mark.parametrize("line", [
    "adb shell",
    "adb logcat",
    "adb shell logcat",
    "adb shell getevent",
    "adb shell top",
    "adb shell screenrecord /sdcard/x.mp4",
    "adb wait-for-device devices",
])
def test_commands_that_never_finish_are_refused(line):
    with pytest.raises(ConsoleError):
        build(line, None)


def test_the_limited_forms_of_those_commands_are_allowed():
    assert build("adb logcat -d", None) == ("adb", ["logcat", "-d"])
    assert build("adb shell top -n 1", None) == ("adb", ["shell", "top", "-n", "1"])
    assert build("adb shell getevent -p", None) == ("adb", ["shell", "getevent", "-p"])


def test_run_line_uses_the_given_programs_and_a_time_limit(monkeypatch):
    seen = {}

    def fake_run(args, *, timeout):
        seen["args"], seen["timeout"] = args, timeout
        return "result"

    monkeypatch.setattr(console, "run", fake_run)

    assert run_line("adb devices", None, adb="C:/tools/adb.exe", fastboot="C:/tools/fastboot.exe") == "result"
    assert seen["args"] == ["C:/tools/adb.exe", "devices"]
    assert seen["timeout"] == console.TIMEOUT
