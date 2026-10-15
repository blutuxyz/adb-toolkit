"""Settings: the light and dark theme, each shown with a drawing of the app layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.settings import DARK, LIGHT
from adb_toolkit.ui.theme import (
    ICON_INLINE,
    PALETTES,
    RADIUS_CARD,
    RADIUS_INSET,
    RADIUS_PILL,
    RADIUS_TILE,
    SCROLL_PADDING,
    SECTION_GAP,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XS,
    Palette,
    palette,
)
from adb_toolkit.ui.i18n import LANGUAGE_NAMES, t
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import PillGroup, card, hue_color, ripple, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

# mode, label, icon, hue
_THEME_LABELS = (
    (LIGHT, "Light", ft.Icons.LIGHT_MODE_OUTLINED, "amber"),
    (DARK, "Dark", ft.Icons.DARK_MODE_OUTLINED, "violet"),
)
_SIZE_LABELS = (("small", "Small"), ("default", "Default"), ("large", "Large"))
_PREVIEW_WIDTH = 240
_PREVIEW_HEIGHT = 150
_CHOICE_WIDTH = _PREVIEW_WIDTH + 2 * SPACE_L


class SettingsView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        choices = ft.Row([self._choice(*entry) for entry in _THEME_LABELS], spacing=SPACE_L)
        self.body = ft.ListView(
            [
                card(
                    t("Appearance"),
                    [choices],
                    description=t("Light or dark. The change applies at once."),
                    icon=ft.Icons.PALETTE_OUTLINED,
                    hue="violet",
                ),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.body.controls.extend(self._preference_cards())
        self.control = screen_frame(
            t("Settings"), self.body, subtitle=t("How the window looks."), icon=ft.Icons.TUNE, hue="amber"
        )

    def _preference_cards(self) -> list[ft.Control]:
        """The text size and language cards. A choice is saved and applied at once, and rebuilds the window."""
        settings = self.window.session.settings
        sizes = PillGroup(
            tuple((key, t(label)) for key, label in _SIZE_LABELS),
            settings.font_scale,
            lambda key: self.window.page.run_task(self.window.change_settings, font_scale=key),
        )
        languages = PillGroup(
            tuple(LANGUAGE_NAMES.items()),
            settings.language,
            lambda code: self.window.page.run_task(self.window.change_settings, language=code),
        )
        return [
            card(
                t("Text size"),
                [sizes.control],
                description=t("Makes the text on every screen larger or smaller."),
                icon=ft.Icons.FORMAT_SIZE,
                hue="blue",
            ),
            card(
                t("Language"),
                [languages.control],
                description=t("The language of the window. Messages from adb and fastboot stay in English."),
                icon=ft.Icons.LANGUAGE,
                hue="green",
            ),
        ]

    async def activate(self) -> None:
        self.window.update()

    def _choice(self, mode: str, label: str, icon: str, hue: str) -> ft.Container:
        colors = palette()
        selected = self.window.session.settings.theme_mode == mode
        indicator = ft.Icons.RADIO_BUTTON_CHECKED if selected else ft.Icons.RADIO_BUTTON_UNCHECKED
        return ft.Container(
            width=_CHOICE_WIDTH,
            padding=SPACE_L,
            border_radius=RADIUS_CARD,
            bgcolor=colors.background,
            border=ft.Border.all(2 if selected else 1, colors.accent if selected else colors.line),
            ink=True,
            ink_color=ripple(),
            on_click=lambda _, value=mode: self.window.page.run_task(self.window.set_theme_mode, value),
            content=ft.Column(
                [
                    _layout_preview(PALETTES[mode]),
                    ft.Container(height=SPACE_M),
                    ft.Row(
                        [
                            ft.Icon(indicator, size=ICON_INLINE, color=colors.accent if selected else colors.muted),
                            ft.Icon(icon, size=ICON_INLINE, color=hue_color(hue)),
                            text(t(label), strong=selected),
                        ],
                        spacing=SPACE_S,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
                tight=True,
            ),
        )


def _layout_preview(colors: Palette) -> ft.Container:
    """A miniature of the real window: the sidebar with its picker and groups, and a content card."""

    def bar(width: float, color: str, height: float = 6) -> ft.Container:
        return ft.Container(width=width, height=height, border_radius=height / 2, bgcolor=color)

    def nav(selected: bool) -> ft.Container:
        return ft.Container(
            height=18,
            padding=ft.Padding.symmetric(horizontal=SPACE_S),
            border_radius=RADIUS_INSET,
            bgcolor=colors.accent_soft if selected else None,
            alignment=ft.Alignment.CENTER_LEFT,
            content=bar(40 if selected else 28, colors.on_accent_soft if selected else colors.muted, height=5),
        )

    sidebar = ft.Container(
        width=78,
        bgcolor=colors.bar,
        border=ft.Border.only(right=ft.BorderSide(1, colors.line)),
        padding=ft.Padding.symmetric(horizontal=SPACE_S, vertical=SPACE_S),
        content=ft.Column(
            [
                ft.Row([ft.Container(width=14, height=14, border_radius=RADIUS_INSET, bgcolor=colors.accent)], spacing=0),
                ft.Container(height=SPACE_S),
                ft.Container(
                    height=18,
                    border_radius=RADIUS_PILL,
                    border=ft.Border.all(1, colors.line),
                    bgcolor=colors.background,
                    padding=ft.Padding.symmetric(horizontal=SPACE_S),
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=bar(44, colors.muted, height=5),
                ),
                ft.Container(height=SPACE_S),
                nav(True),
                nav(False),
                nav(False),
                ft.Container(height=SPACE_S),
                nav(False),
            ],
            spacing=SPACE_XS,
            tight=True,
        ),
    )
    content = ft.Container(
        expand=True,
        bgcolor=colors.background,
        padding=SPACE_S,
        content=ft.Column(
            [
                bar(70, colors.text, height=7),
                ft.Container(height=SPACE_S),
                ft.Container(
                    expand=True,
                    border_radius=RADIUS_INSET,
                    bgcolor=colors.panel,
                    border=ft.Border.all(1, colors.line),
                    padding=SPACE_S,
                    content=ft.Column(
                        [bar(92, colors.text, height=6), ft.Container(height=SPACE_S), bar(120, colors.line, height=5)],
                        spacing=0,
                    ),
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )
    return ft.Container(
        width=_PREVIEW_WIDTH,
        height=_PREVIEW_HEIGHT,
        border_radius=RADIUS_TILE,
        border=ft.Border.all(1, colors.line),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Row([sidebar, content], spacing=0, expand=True),
    )
