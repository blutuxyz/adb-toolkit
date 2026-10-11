import asyncio
import time
from types import SimpleNamespace

import pytest

from adb_toolkit.ui.window import Window


class _Page:
    def __init__(self) -> None:
        self.updates = 0

    def update(self) -> None:
        self.updates += 1


def _window_stub() -> Window:
    """Only the parts of Window that run_blocking uses. The real class needs a live Flet page."""
    return SimpleNamespace(page=_Page())  # type: ignore[return-value]


def test_forwards_positional_and_keyword_arguments_to_the_worker():
    def uninstall(serial, package, *, system):
        return f"{serial}:{package}:{system}"

    result = asyncio.run(Window.run_blocking(_window_stub(), uninstall, "R58", "com.x", system=True))

    assert result == "R58:com.x:True"


def test_returns_the_worker_result():
    assert asyncio.run(Window.run_blocking(_window_stub(), lambda: 42)) == 42


def test_worker_errors_reach_the_caller():
    def broken():
        raise ValueError("adb is gone")

    with pytest.raises(ValueError, match="adb is gone"):
        asyncio.run(Window.run_blocking(_window_stub(), broken))


def test_on_tick_runs_while_the_worker_is_busy_and_the_page_is_refreshed():
    window = _window_stub()
    ticks = []

    def slow():
        time.sleep(0.35)
        return "done"

    result = asyncio.run(Window.run_blocking(window, slow, on_tick=lambda: ticks.append(1)))

    assert result == "done"
    assert len(ticks) >= 2
    assert window.page.updates == len(ticks)
