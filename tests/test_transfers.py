"""The adb and fastboot commands behind the new screens: what they run, and how their results are judged."""

from adb_toolkit.core import adb as adb_module
from adb_toolkit.core import fastboot as fastboot_module
from adb_toolkit.core.adb import (
    MAX_RECORDING_SECONDS,
    PHONE_RECORDING,
    PHONE_SCREENSHOT,
    Adb,
    install_succeeded,
    sideload_succeeded,
)
from adb_toolkit.core.fastboot import Fastboot, parse_partitions
from adb_toolkit.core.process import CommandResult

PARTITIONS = (
    "(bootloader) partition-size:boot_a: 0x4000000\n"
    "(bootloader) partition-type:boot_a: raw\n"
    "(bootloader) partition-size:system_a: 0x1\n"
    "(bootloader) partition-size:boot_a: 0x4000000\n"
    "Finished. Total time: 0.1s\n"
)


def _ok(args=()) -> CommandResult:
    return CommandResult(tuple(args), 0)


def test_install_push_pull_and_sideload_run_the_streamed_commands(monkeypatch):
    seen = []
    monkeypatch.setattr(adb_module, "stream", lambda args, on_line, **kwargs: seen.append(list(args)) or _ok(args))
    adb = Adb(executable="adb")

    adb.install_apk("S1", "app.apk")
    adb.push("S1", "a.txt", "/sdcard/a.txt")
    adb.pull("S1", "/sdcard/a.txt", "a.txt")
    adb.sideload("S1", "rom.zip")

    assert seen == [
        ["adb", "-s", "S1", "install", "-r", "app.apk"],
        ["adb", "-s", "S1", "push", "a.txt", "/sdcard/a.txt"],
        ["adb", "-s", "S1", "pull", "/sdcard/a.txt", "a.txt"],
        ["adb", "-s", "S1", "sideload", "rom.zip"],
    ]


def test_a_screenshot_is_taken_on_the_phone_pulled_and_the_copy_removed(monkeypatch):
    shell_calls, pulls = [], []
    monkeypatch.setattr(Adb, "_run", lambda self, *args, **kwargs: shell_calls.append(args) or _ok(args))
    monkeypatch.setattr(Adb, "pull",
                        lambda self, serial, remote, local, on_line=None: pulls.append((remote, local)) or _ok())

    Adb(executable="adb").screenshot("S1", "shot.png")

    assert shell_calls == [
        ("-s", "S1", "shell", "screencap", "-p", PHONE_SCREENSHOT),
        ("-s", "S1", "shell", "rm", "-f", PHONE_SCREENSHOT),
    ]
    assert pulls == [(PHONE_SCREENSHOT, "shot.png")]


def test_a_recording_is_capped_at_the_phone_limit(monkeypatch):
    seen = []
    monkeypatch.setattr(adb_module, "stream", lambda args, on_line, **kwargs: seen.append(list(args)) or _ok(args))
    monkeypatch.setattr(Adb, "pull", lambda self, serial, remote, local, on_line=None: _ok())
    monkeypatch.setattr(Adb, "_run", lambda self, *args, **kwargs: _ok(args))

    Adb(executable="adb").record("S1", "rec.mp4", 999)

    assert seen == [["adb", "-s", "S1", "shell", "screenrecord", "--time-limit",
                     str(MAX_RECORDING_SECONDS), PHONE_RECORDING]]


def test_install_is_judged_from_its_output_not_its_exit_code():
    assert install_succeeded("Performing Streamed Install\nSuccess")
    assert not install_succeeded("Failure [INSTALL_FAILED_VERSION_DOWNGRADE]")


def test_sideload_is_judged_by_the_transfer_total_adb_prints():
    assert sideload_succeeded("serving: 'rom.zip'  (~100%)\nTotal xfer: 1.00x")
    assert not sideload_succeeded("adb: failed to read command: No error")


def test_partition_names_come_from_the_size_lines_without_repeats():
    assert parse_partitions(PARTITIONS) == ["boot_a", "system_a"]


def test_partitions_are_read_from_the_output_because_fastboot_writes_to_stderr(monkeypatch):
    monkeypatch.setattr(Fastboot, "_run", lambda self, *args, **kwargs: CommandResult(args, 0, "", PARTITIONS))

    assert Fastboot(executable="fastboot").partitions("F1") == ["boot_a", "system_a"]


def test_flash_writes_the_image_to_the_named_partition(monkeypatch):
    seen = []
    monkeypatch.setattr(fastboot_module, "stream", lambda args, on_line: seen.append(list(args)) or _ok(args))

    Fastboot(executable="fastboot").flash("F1", "boot_a", "boot.img")

    assert seen == [["fastboot", "-s", "F1", "flash", "boot_a", "boot.img"]]
