"""Base class for the screens shown in the content area."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class View:
    """A screen. Subclasses build `control` and fill it in `activate`."""

    def __init__(self, window: Window) -> None:
        self.window = window
        self.control: ft.Control = ft.Container()

    async def activate(self) -> None:
        """Called every time the screen is opened."""

    async def on_devices_changed(self) -> None:
        """Called when the device list or the selection changes while this screen is open."""
        await self.activate()
