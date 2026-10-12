"""The 'Updating scrcpy' flow: the screen replaces the window, shows failures, and offers retry or a way out."""

import asyncio
from pathlib import Path

import pytest

from adb_toolkit.core import scrcpy_install
from adb_toolkit.core.scrcpy_install import RemoteScrcpy, ScrcpyInstallError
from adb_toolkit.core.versions import Version
from adb_toolkit.ui import window as window_module
from adb_toolkit.ui.views.setup import SetupView
from adb_toolkit.ui.window import Window

REMOTE = RemoteScrcpy(Version(5, 0, 1), "https://example.test/scrcpy.zip", 10, "a" * 64)


class _Page:
    def __init__(self) -> None:
        self.controls: list = []

    def update(self) -> None:
        pass


class _Window:
    """Only the parts of Window that update_scrcpy uses. The real class needs a live Flet page."""

    run_blocking = Window.run_blocking

    def __init__(self) -> None:
        self.page = _Page()
        self.shell = None
        self._covered = False
        self.screens: list[SetupView] = []

    def update(self) -> None:
        pass


@pytest.fixture
def window(monkeypatch):
    stub = _Window()

    class RecordingSetupView(SetupView):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            stub.screens.append(self)

    monkeypatch.setattr(window_module, "SetupView", RecordingSetupView)
    monkeypatch.setattr(window_module, "managed_executable", lambda: Path("missing-scrcpy.exe"))
    return stub


def _run(window: _Window, remote=REMOTE) -> asyncio.Task:
    return asyncio.ensure_future(Window.update_scrcpy(window, remote))


def test_a_good_download_shows_the_screen_and_reports_success(window, monkeypatch):
    seen = {}

    def install(remote, progress):
        seen["controls"] = list(window.page.controls)
        seen["covered"] = window._covered
        progress(5, 10)

    monkeypatch.setattr(scrcpy_install, "install", install)

    assert asyncio.run(Window.update_scrcpy(window, REMOTE)) is True
    assert seen["controls"] == [window.screens[0].control]
    assert seen["covered"] is True
    assert window._covered is False
    assert window.screens[0]._skip.content.value == "Continue without scrcpy"


def test_the_release_is_looked_up_when_none_was_given(window, monkeypatch):
    monkeypatch.setattr(scrcpy_install, "fetch_latest", lambda: REMOTE)
    installed = []
    monkeypatch.setattr(scrcpy_install, "install", lambda remote, progress: installed.append(remote))

    assert asyncio.run(Window.update_scrcpy(window, None)) is True
    assert installed == [REMOTE]


def test_a_failed_download_is_shown_and_the_user_can_leave(window, monkeypatch):
    def install(remote, progress):
        raise ScrcpyInstallError("Download failed: offline")

    monkeypatch.setattr(scrcpy_install, "install", install)

    async def scenario() -> bool:
        task = _run(window)
        while not (window.screens and window.screens[0]._actions.visible):
            await asyncio.sleep(0.01)
        assert window.screens[0]._status.value == "Download failed: offline"
        window.screens[0]._skip.on_click(None)
        return await task

    assert asyncio.run(scenario()) is False
    assert window._covered is False


def test_try_again_runs_the_download_a_second_time(window, monkeypatch):
    attempts = []

    def install(remote, progress):
        attempts.append(remote)
        if len(attempts) == 1:
            raise ScrcpyInstallError("Download failed: offline")

    monkeypatch.setattr(scrcpy_install, "install", install)

    async def scenario() -> bool:
        task = _run(window)
        while not (window.screens and window.screens[0]._actions.visible):
            await asyncio.sleep(0.01)
        window.screens[0]._retry.on_click(None)
        return await task

    assert asyncio.run(scenario()) is True
    assert len(attempts) == 2
