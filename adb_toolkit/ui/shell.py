"""Main layout: sidebar on the left, top bar above the content area."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.ui.sidebar import Sidebar
from adb_toolkit.ui.theme import GUTTER, MOTION_SCREEN_MS, SECTION_GAP, SPACE_XL, palette
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
        self.sidebar = Sidebar(lambda key: window.page.run_task(self.open, key)) # type: ignore
        self.topbar = TopBar(
            on_pick=lambda serial: window.page.run_task(window.select_device, serial), # type: ignore
            on_connect=lambda: window.connect_over_wifi_dialog(),
            on_refresh=lambda: window.page.run_task(window.refresh_devices), # type: ignore
        )
        # The switcher only animates when the content's key changes, so each screen gets its own key below.
        self._switcher = ft.AnimatedSwitcher(
            content=ft.Container(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=MOTION_SCREEN_MS,
            reverse_duration=MOTION_SCREEN_MS,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            expand=True,
        )
        for key, view in self.views.items():
            view.control.key = key
        self._body = ft.Container(
            expand=True,
            padding=ft.Padding.only(left=GUTTER, right=GUTTER, top=SECTION_GAP, bottom=SPACE_XL),
            content=self._switcher,
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
        self._switcher.content = view.control
        self.window.update()
        await view.activate()

    async def devices_changed(self) -> None:
        """Redraw the device picker and let the open screen react."""
        self.topbar.show(self.window.session)
        await self.views[self.current].on_devices_changed()

    def render_topbar(self) -> None:
        self.topbar.show(self.window.session)

    def scrcpy_changed(self) -> None:
        """scrcpy was installed or updated. The screen section shows whether it can start."""
        self.views["adb"].mirror.refresh()

    def updates_changed(self) -> None:
        session = self.window.session
        self.sidebar.set_update_badge(session.update_available or session.app_update_available)
        if self.current == "updates":
            self.views["updates"].refresh()
