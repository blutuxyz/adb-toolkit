"""About: what the app is and who made it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import APP_NAME, APP_VERSION, CREATOR_NAME, CREATOR_URL, PROJECT_URL
from adb_toolkit.ui.theme import FONT_SEMIBOLD, ROW_PADDING, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import brand_mark, hairline, icon_tile, ripple, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class AboutView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self.control = ft.Column(
            [
                ft.Row(
                    [
                        brand_mark(56),
                        ft.Column(
                            [
                                text(APP_NAME, size=26, font=FONT_SEMIBOLD),
                                text(f"Version {APP_VERSION}", mono=True, color=colors.muted),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                    ],
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=32),
                hairline(),
                _link_row("Website", CREATOR_URL, self._open(CREATOR_URL), ft.Icons.LANGUAGE, "blue"),
                hairline(),
                _link_row("Source code", PROJECT_URL, self._open(PROJECT_URL), ft.Icons.CODE, "violet"),
                hairline(),
                ft.Container(height=24),
                text(f"Made by {CREATOR_NAME}", color=colors.muted),
            ],
            expand=True,
            spacing=0,
        )

    def _open(self, url: str):
        return lambda _: self.window.page.run_task(self.window.open_url, url)


def _link_row(label: str, url: str, on_click, icon: str, hue: str) -> ft.Container:
    colors = palette()
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        ink=True,
        ink_color=ripple(),
        on_click=on_click,
        content=ft.Row(
            [
                icon_tile(icon, hue),
                ft.Column(
                    [
                        text(label, size=15, font=FONT_SEMIBOLD),
                        text(url.replace("https://", ""), mono=True, size=13, color=colors.muted),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
                ft.Icon(ft.Icons.OPEN_IN_NEW, size=18, color=colors.muted),
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
