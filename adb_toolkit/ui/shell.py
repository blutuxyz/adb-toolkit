"""Main layout: sidebar on the left, top bar above the content area."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.ui.sidebar import Sidebar
from adb_toolkit.ui.theme import palette
from adb_toolkit.ui.topbar import TopBar
from adb_toolkit.ui.views.about import AboutView
from adb_toolkit.ui.views.adb_tools import AdbToolsView
from adb_toolkit.ui.views.apps import AppsView
from adb_toolkit.ui.views.fastboot_tools import FastbootToolsView
from adb_toolkit.ui.views.settings import SettingsView
from adb_toolkit.ui.views.updates import UpdatesView

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class Shell:
    def __init__(self, window: Window) -> None:
        self.window = window
        self.current = "apps"
        self.views = {
            "apps": AppsView(window),
            "adb": AdbToolsView(window),
            "fastboot": FastbootToolsView(window),
            "settings": SettingsView(window),
            "updates": UpdatesView(window),
            "about": AboutView(window),
        }
        self.sidebar = Sidebar(lambda key: window.page.run_task(self.open, key))
        self.topbar = TopBar(
            on_pick=lambda serial: window.page.run_task(window.select_device, serial),
            on_connect=lambda: window.connect_over_wifi_dialog(),
            on_refresh=lambda: window.page.run_task(window.refresh_devices),
        )
        self._body = ft.Container(
            expand=True,
            padding=ft.Padding.only(left=36, right=36, top=32, bottom=24),
        )
        colors = palette()
        self.root = ft.Row(
            [
                self.sidebar.control,
                ft.Container(width=1, bgcolor=colors.line),
                ft.Column([self.topbar.control, self._body], expand=True, spacing=0),
            ],
            expand=True,
            spacing=0,
        )

    async def open(self, key: str) -> None:
        """Show a screen. The window must already be on the page."""
        self.current = key
        self.sidebar.select(key)
        view = self.views[key]
        self._body.content = view.control
        self.window.update()
        await view.activate()

    async def devices_changed(self) -> None:
        """Redraw the device picker and let the open screen react."""
        self.topbar.show(self.window.session)
        await self.views[self.current].on_devices_changed()

    def render_topbar(self) -> None:
        self.topbar.show(self.window.session)

    def updates_changed(self) -> None:
        self.sidebar.set_update_badge(self.window.session.update_available)
        if self.current == "updates":
            self.views["updates"].refresh()
