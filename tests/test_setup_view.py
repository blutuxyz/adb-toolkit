from types import SimpleNamespace

from adb_toolkit.core.platform_tools import Progress
from adb_toolkit.ui.views.setup import SetupView


def _view(skip=None) -> SetupView:
    window = SimpleNamespace(update=lambda: None)
    return SetupView(window, title="Updating scrcpy", body="body", retry=lambda: None, skip=skip, skip_label="Skip")


def test_the_screen_starts_by_checking_the_release():
    view = _view()

    assert view._status.value == "Checking the latest release"
    assert view._progress.value is None
    assert view._actions.visible is False


def test_a_download_shows_how_far_it_got():
    view = _view()

    view.show_progress(Progress(done=5_500_000, total=11_000_000))

    assert view._progress.value == 0.5
    assert view._status.value == "Downloading 5.5 of 11.0 MB"


def test_a_finished_download_says_it_is_installing():
    view = _view()

    view.show_progress(Progress(done=11_000_000, total=11_000_000))

    assert view._status.value == "Installing"
    assert view._progress.value is None


def test_a_failure_offers_another_try_and_reset_hides_it_again():
    view = _view(skip=lambda: None)

    view.show_error("Download failed: offline")

    assert view._status.value == "Download failed: offline"
    assert view._actions.visible is True
    assert view._skip.visible is True

    view.reset()

    assert view._actions.visible is False
    assert view._status.value == "Checking the latest release"


def test_without_a_way_out_the_skip_button_stays_hidden():
    assert _view(skip=None)._skip.visible is False
