"""About: what the app is and who made it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import APP_NAME, APP_VERSION, CREATOR_NAME, CREATOR_URL, PROJECT_URL
from adb_toolkit.ui.theme import ICON_INLINE, ROW_PADDING, SCROLL_PADDING, SECTION_GAP, SPACE_M, TYPE_CAPTION, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import brand_mark, hairline, hue_color, ripple, screen_frame, sections, spec_section, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class AboutView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        links = [
            _link_row("Website", CREATOR_URL, self._open(CREATOR_URL), ft.Icons.LANGUAGE, "blue"),
            hairline(),
            _link_row("Source code", PROJECT_URL, self._open(PROJECT_URL), ft.Icons.CODE, "violet"),
        ]
        self.body = ft.ListView(
            [
                ft.Row(
                    [
                        brand_mark(56),
                        ft.Column(
                            [
                                text(f"Version {APP_VERSION}", mono=True, color=colors.muted),
                                text(f"Made by {CREATOR_NAME}", color=colors.muted),
                            ],
                            spacing=0,
                            tight=True,
                        ),
                    ],
                    spacing=SPACE_M,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                *sections(spec_section("Links", links, description="Where the project lives.")),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(APP_NAME, self.body, subtitle="A workbench for adb and fastboot.", hue="rose")

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
                ft.Icon(icon, size=ICON_INLINE, color=hue_color(hue)),
                ft.Column(
                    [
                        text(label),
                        text(url.replace("https://", ""), mono=True, size=TYPE_CAPTION, color=colors.muted),
                    ],
                    spacing=0,
                    tight=True,
                    expand=True,
                ),
                ft.Icon(ft.Icons.OPEN_IN_NEW, size=ICON_INLINE, color=colors.muted),
            ],
            spacing=SPACE_M,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
