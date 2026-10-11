"""The Updates buttons must hand coroutine functions to Page.run_task, which rejects anything else."""

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from adb_toolkit.ui.views import updates
from adb_toolkit.ui.views.updates import UpdatesView


@pytest.fixture
def run_tasks(monkeypatch):
    """Build the view with a fake page that records what each button sends to run_task."""
    monkeypatch.setattr(updates, "managed_binary", lambda name: Path(name))
    sent = []
    page = SimpleNamespace(run_task=lambda handler, *args, **kwargs: sent.append(handler))
    view = UpdatesView(SimpleNamespace(session=None, page=page))
    return view, sent


def test_check_button_sends_a_coroutine_function(run_tasks):
    view, sent = run_tasks
    view._check.on_click(None)
    assert len(sent) == 1
    assert inspect.iscoroutinefunction(sent[0])


def test_install_button_sends_a_coroutine_function(run_tasks):
    view, sent = run_tasks
    view._install.on_click(None)
    assert len(sent) == 1
    assert inspect.iscoroutinefunction(sent[0])


def test_app_release_button_sends_a_coroutine_function(run_tasks):
    view, sent = run_tasks
    view._app_button.on_click(None)
    assert len(sent) == 1
    assert inspect.iscoroutinefunction(sent[0])
