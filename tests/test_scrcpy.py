from pathlib import Path

import pytest

from adb_toolkit.core import paths, scrcpy as scrcpy_module
from adb_toolkit.core.scrcpy import MirrorOptions, Scrcpy, ScrcpyError, build_args


class _FakeProcess:
    """Stands in for a running scrcpy window. exit_code is None while the window is open."""

    def __init__(self) -> None:
        self.exit_code: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True
        self.exit_code = 1

    def kill(self) -> None:
        self.killed = True
        self.exit_code = 1

    def wait(self, timeout: float | None = None) -> int | None:
        return self.exit_code


@pytest.fixture
def launches(monkeypatch):
    """Record every scrcpy launch instead of starting a window."""
    started = []

    def fake_popen(args, **kwargs):
        process = _FakeProcess()
        started.append((args, kwargs, process))
        return process

    monkeypatch.setattr(scrcpy_module.subprocess, "Popen", fake_popen)
    return started


@pytest.fixture
def executable(tmp_path) -> Path:
    path = tmp_path / "scrcpy.exe"
    path.touch()
    return path


def _scrcpy(executable: Path, tmp_path: Path) -> Scrcpy:
    return Scrcpy(executable=executable, log_file=tmp_path / "scrcpy.log")


def test_the_default_options_keep_the_phone_awake_and_nothing_else():
    args = build_args("scrcpy.exe", "R58", MirrorOptions(), title="ADB Toolkit - R58")

    assert args == ["scrcpy.exe", "-s", "R58", "--window-title=ADB Toolkit - R58", "--stay-awake"]


def test_each_option_adds_its_own_flag():
    options = MirrorOptions(max_size=1080, stay_awake=False, screen_off=True, show_touches=True)

    args = build_args("scrcpy.exe", "R58", options, title="t")

    assert "--max-size=1080" in args
    assert "--turn-screen-off" in args
    assert "--show-touches" in args
    assert "--stay-awake" not in args


def test_the_toolkit_folder_is_preferred_over_path(monkeypatch, tmp_path):
    managed = tmp_path / "scrcpy" / scrcpy_module.EXECUTABLE_NAME
    managed.parent.mkdir()
    managed.touch()
    monkeypatch.setattr(paths, "scrcpy_dir", lambda: managed.parent)
    monkeypatch.setattr(scrcpy_module.shutil, "which", lambda name: r"C:\other\scrcpy.exe")

    assert Scrcpy(log_file=tmp_path / "log").find() == managed


def test_path_is_used_when_the_toolkit_has_no_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "scrcpy_dir", lambda: tmp_path / "missing")
    monkeypatch.setattr(scrcpy_module.shutil, "which", lambda name: r"C:\tools\scrcpy.exe")

    assert Scrcpy(log_file=tmp_path / "log").find() == Path(r"C:\tools\scrcpy.exe")


def test_nothing_is_found_when_scrcpy_is_not_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "scrcpy_dir", lambda: tmp_path / "missing")
    monkeypatch.setattr(scrcpy_module.shutil, "which", lambda name: None)

    assert Scrcpy(log_file=tmp_path / "log").find() is None


def test_start_names_the_phone_and_the_adb_it_should_use(launches, executable, tmp_path):
    _scrcpy(executable, tmp_path).start("R58", MirrorOptions(), r"C:\platform-tools\adb.exe")

    args, kwargs, _ = launches[0]
    assert args[:3] == [str(executable), "-s", "R58"]
    assert kwargs["env"]["ADB"] == r"C:\platform-tools\adb.exe"


def test_a_second_mirror_of_the_same_phone_is_refused(launches, executable, tmp_path):
    scrcpy = _scrcpy(executable, tmp_path)
    scrcpy.start("R58", MirrorOptions(), "adb")

    with pytest.raises(ScrcpyError, match="already"):
        scrcpy.start("R58", MirrorOptions(), "adb")


def test_start_says_so_when_scrcpy_is_missing(tmp_path):
    scrcpy = Scrcpy(executable=tmp_path / "missing.exe", log_file=tmp_path / "log")

    with pytest.raises(ScrcpyError, match="not installed"):
        scrcpy.start("R58", MirrorOptions(), "adb")


def test_running_follows_the_window(launches, executable, tmp_path):
    scrcpy = _scrcpy(executable, tmp_path)
    scrcpy.start("R58", MirrorOptions(), "adb")
    _, _, process = launches[0]

    assert scrcpy.running("R58") is True

    process.exit_code = 0

    assert scrcpy.running("R58") is False


def test_stop_closes_the_window(launches, executable, tmp_path):
    scrcpy = _scrcpy(executable, tmp_path)
    scrcpy.start("R58", MirrorOptions(), "adb")
    _, _, process = launches[0]

    scrcpy.stop("R58")

    assert process.terminated is True
    assert scrcpy.running("R58") is False


def test_log_tail_keeps_the_last_lines(tmp_path):
    log_file = tmp_path / "scrcpy.log"
    log_file.write_text("one\n\ntwo\nthree\nfour\n", encoding="utf-8")

    assert Scrcpy(log_file=log_file).log_tail(lines=2) == "three\nfour"


def test_log_tail_is_empty_before_scrcpy_has_run(tmp_path):
    assert Scrcpy(log_file=tmp_path / "missing.log").log_tail() == ""
