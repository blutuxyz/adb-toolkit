"""Settings: the light and dark theme, each shown with a drawing of the app layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.settings import DARK, LIGHT
from adb_toolkit.ui.theme import (
    FONT_REGULAR,
    FONT_SEMIBOLD,
    PALETTES,
    RADIUS_CARD,
    RADIUS_INSET,
    RADIUS_TILE,
    SCROLL_PADDING,
    SECTION_GAP,
    Palette,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import hue_color, ripple, status_dot, text, title_block

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

# mode, label, icon, hue
_THEME_LABELS = (
    (LIGHT, "Light", ft.Icons.LIGHT_MODE_OUTLINED, "amber"),
    (DARK, "Dark", ft.Icons.DARK_MODE_OUTLINED, "violet"),
)
_PREVIEW_WIDTH = 240
_PREVIEW_HEIGHT = 140
_CARD_PADDING = 16


class SettingsView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.control = ft.ListView(
            [
                title_block("Settings"),
                ft.Container(height=SECTION_GAP),
                text("Appearance", size=18, font=FONT_SEMIBOLD),
                ft.Container(height=16),
                ft.Row([self._choice(*entry) for entry in _THEME_LABELS], spacing=20),
            ],
            expand=True,
            spacing=0,
            padding=SCROLL_PADDING,
        )

    async def activate(self) -> None:
        self.window.update()

    def _choice(self, mode: str, label: str, icon: str, hue: str) -> ft.Container:
        colors = palette()
        selected = self.window.session.settings.theme_mode == mode
        indicator = ft.Icons.RADIO_BUTTON_CHECKED if selected else ft.Icons.RADIO_BUTTON_UNCHECKED
        return ft.Container(
            width=_PREVIEW_WIDTH + 2 * _CARD_PADDING,
            padding=_CARD_PADDING,
            border_radius=RADIUS_CARD,
            bgcolor=colors.panel,
            border=ft.Border.all(2 if selected else 1, colors.accent if selected else colors.line),
            ink=True,
            ink_color=ripple(),
            on_click=lambda _, value=mode: self.window.page.run_task(self.window.set_theme_mode, value),
            content=ft.Column(
                [
                    _layout_preview(PALETTES[mode]),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Icon(indicator, size=18, color=colors.accent if selected else colors.muted),
                            ft.Icon(icon, size=18, color=hue_color(hue)),
                            text(label, size=14, font=FONT_SEMIBOLD if selected else FONT_REGULAR),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
                tight=True,
            ),
        )


def _layout_preview(colors: Palette) -> ft.Container:
    """A miniature of the real window: sidebar, top bar with a device chip, and a content card."""

    def pill(width: float, color: str, height: float = 7) -> ft.Container:
        return ft.Container(width=width, height=height, border_radius=height / 2, bgcolor=color)

    sidebar = ft.Container(
        width=64,
        bgcolor=colors.background,
        padding=ft.Padding.symmetric(horizontal=9, vertical=12),
        content=ft.Column(
            [
                ft.Container(width=16, height=16, border_radius=RADIUS_INSET, bgcolor=colors.accent),
                ft.Container(height=8),
                ft.Container(
                    height=16,
                    border_radius=8,
                    bgcolor=colors.accent_soft,
                    padding=ft.Padding.symmetric(horizontal=6),
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=pill(36, colors.on_accent_soft),
                ),
                ft.Container(height=6),
                pill(40, colors.line),
                ft.Container(height=6),
                pill(32, colors.line),
            ],
            spacing=0,
        ),
    )
    top_bar = ft.Container(
        height=28,
        bgcolor=colors.bar,
        padding=ft.Padding.symmetric(horizontal=10),
        alignment=ft.Alignment.CENTER_LEFT,
        content=ft.Row(
            [
                status_dot(colors.accent, size=6),
                ft.Container(
                    width=92,
                    height=16,
                    border_radius=8,
                    bgcolor=colors.panel,
                    border=ft.Border.all(1, colors.line),
                    alignment=ft.Alignment.CENTER_LEFT,
                    padding=ft.Padding.symmetric(horizontal=6),
                    content=pill(44, colors.muted, height=5),
                ),
            ],
            spacing=8,
        ),
    )
    card = ft.Container(
        height=54,
        border_radius=RADIUS_INSET,
        bgcolor=colors.panel,
        border=ft.Border.all(1, colors.line),
        padding=ft.Padding.symmetric(horizontal=10, vertical=9),
        content=ft.Column(
            [pill(92, colors.text, height=6), ft.Container(height=8), pill(120, colors.line, height=5), ft.Container(height=5), pill(84, colors.line, height=5)],
            spacing=0,
        ),
    )
    content = ft.Container(
        expand=True,
        bgcolor=colors.background,
        padding=10,
        content=ft.Column([pill(70, colors.text, height=8), ft.Container(height=10), card], spacing=0),
    )
    return ft.Container(
        width=_PREVIEW_WIDTH,
        height=_PREVIEW_HEIGHT,
        border_radius=RADIUS_TILE,
        border=ft.Border.all(1, colors.line),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Row(
            [
                sidebar,
                ft.Container(width=1, bgcolor=colors.line),
                ft.Column([top_bar, ft.Container(height=1, bgcolor=colors.line), content], spacing=0, expand=True),
            ],
            spacing=0,
            expand=True,
        ),
    )
