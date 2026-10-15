"""About: what the app is and who made it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import APP_NAME, APP_VERSION, CREATOR_NAME, CREATOR_URL, PROJECT_URL
from adb_toolkit.ui.theme import (
    CARD_PADDING,
    ICON_INLINE,
    RADIUS_CARD,
    SCROLL_PADDING,
    SECTION_GAP,
    SPACE_L,
    SPACE_XS,
    TYPE_CAPTION,
    TYPE_DISPLAY,
    palette,
)
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import brand_mark, card, row_item, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class AboutView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        hero = ft.Container(
            padding=CARD_PADDING,
            border_radius=RADIUS_CARD,
            bgcolor=colors.panel,
            border=ft.Border.all(1, colors.line),
            content=ft.Row(
                [
                    brand_mark(64),
                    ft.Column(
                        [
                            text(APP_NAME, size=TYPE_DISPLAY, strong=True),
                            text(t("Version {version}", version=APP_VERSION), size=TYPE_CAPTION, mono=True, color=colors.muted),
                            text(t("Made by {name}", name=CREATOR_NAME), color=colors.muted),
                        ],
                        spacing=SPACE_XS,
                        tight=True,
                    ),
                ],
                spacing=SPACE_L,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        links = card(
            t("Links"),
            [
                row_item(
                    t("Website"),
                    CREATOR_URL.removeprefix("https://"),
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=ICON_INLINE, color=colors.muted),
                    icon=ft.Icons.LANGUAGE,
                    hue="blue",
                    on_click=self._open(CREATOR_URL),
                ),
                row_item(
                    t("Source code"),
                    PROJECT_URL.removeprefix("https://"),
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=ICON_INLINE, color=colors.muted),
                    icon=ft.Icons.CODE,
                    hue="violet",
                    on_click=self._open(PROJECT_URL),
                ),
            ],
            description=t("Where the project lives."),
            divided=True,
        )
        self.body = ft.ListView([hero, links], expand=True, spacing=SECTION_GAP, padding=SCROLL_PADDING)
        self.control = screen_frame(
            APP_NAME,
            self.body,
            subtitle=t("A workbench for adb and fastboot."),
            icon=ft.Icons.INFO_OUTLINE,
            hue="rose",
        )

    def _open(self, url: str):
        return lambda _: self.window.page.run_task(self.window.open_url, url)
