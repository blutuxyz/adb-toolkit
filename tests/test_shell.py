"""The screen area and the clickable containers are wired so that motion and ripples show."""

import asyncio
import dataclasses
from pathlib import Path
from types import SimpleNamespace

import flet as ft

from adb_toolkit.core.settings import AppSettings
from adb_toolkit.ui.shell import Shell
from adb_toolkit.ui.views import updates


def _shell(monkeypatch) -> Shell:
    monkeypatch.setattr(updates, "managed_binary", lambda name: Path(name))
    session = SimpleNamespace(
        settings=AppSettings(),
        local=SimpleNamespace(adb_version=None, fastboot_version=None, installed=False),
        latest=None,
        update_available=False,
        app_update_available=False,
        app_checked=False,
        app_release=None,
        selected_device=None,
        devices=[],
    )
    window = SimpleNamespace(
        session=session,
        page=SimpleNamespace(run_task=lambda *args, **kwargs: None),
        update=lambda: None,
        busy=False,
    )
    return Shell(window)


def _controls(root: ft.Control):
    """Every control under `root`, found by following the fields each control holds."""
    seen = set()
    pending = [root]
    while pending:
        control = pending.pop()
        if id(control) in seen:
            continue
        seen.add(id(control))
        yield control
        for field in dataclasses.fields(control):
            value = getattr(control, field.name, None)
            children = value if isinstance(value, list) else [value]
            pending.extend(child for child in children if isinstance(child, ft.Control))


def test_each_screen_has_its_own_key_so_the_switcher_animates_between_them(monkeypatch):
    shell = _shell(monkeypatch)

    for key, view in shell.views.items():
        assert view.control.key == key


def test_opening_a_screen_puts_it_in_the_switcher(monkeypatch):
    shell = _shell(monkeypatch)
    # Nothing is attached to a page here, so repainting the sidebar has nowhere to go.
    monkeypatch.setattr(ft.Control, "update", lambda self: None)

    asyncio.run(shell.open("fastboot"))

    assert shell._switcher.content is shell.views["fastboot"].control


def test_every_clickable_container_has_a_ripple(monkeypatch):
    shell = _shell(monkeypatch)
    controls = list(_controls(shell.root))
    for view in shell.views.values():
        controls.extend(_controls(view.control))

    clickable = [c for c in controls if isinstance(c, ft.Container) and c.on_click is not None]

    assert clickable, "the sidebar items should be found"
    assert all(c.ink for c in clickable), "a clickable container without ink gives no press feedback"
