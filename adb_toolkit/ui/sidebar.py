"""Left navigation: the tool groups first, then settings and information."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.config import APP_VERSION
from adb_toolkit.ui.theme import FONT_REGULAR, FONT_SEMIBOLD, palette
from adb_toolkit.ui.widgets import brand_mark, hairline, text

TOOL_ITEMS = (
    ("apps", "Apps", ft.Icons.APPS),
    ("adb", "ADB Tools", ft.Icons.TERMINAL),
    ("fastboot", "Fastboot Tools", ft.Icons.FLASH_ON),
)
APP_ITEMS = (
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED),
    ("updates", "Updates", ft.Icons.SYSTEM_UPDATE_ALT),
    ("about", "About", ft.Icons.INFO_OUTLINE),
)


class _NavItem:
    def __init__(self, key: str, label: str, icon: str, on_select: Callable[[str], None]) -> None:
        self.key = key
        self._selected = False
        self._hovered = False
        self._icon = ft.Icon(icon, size=20)
        self._label = text(label)
        self._badge = ft.Container(width=8, height=8, border_radius=4, visible=False)
        self.control = ft.Container(
            content=ft.Row(
                [self._icon, self._label, ft.Container(expand=True), self._badge],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=40,
            padding=ft.Padding.symmetric(horizontal=12),
            border_radius=10,
            on_click=lambda _: on_select(key),
            on_hover=self._on_hover,
        )
        self._paint()

    def select(self, selected: bool) -> None:
        self._selected = selected
        self._repaint()

    def set_badge(self, visible: bool) -> None:
        self._badge.visible = visible
        self._repaint()

    def _on_hover(self, event: ft.HoverEvent) -> None:
        self._hovered = str(event.data).lower() == "true"
        self._repaint()

    def _repaint(self) -> None:
        # Flet sends a child's new colour only when the child itself is updated.
        self._paint()
        for control in (self.control, self._icon, self._label, self._badge):
            control.update()

    def _paint(self) -> None:
        colors = palette()
        if self._selected:
            background, foreground, icon_color, font = colors.accent_soft, colors.on_accent_soft, colors.on_accent_soft, FONT_SEMIBOLD
        else:
            background = colors.panel_high if self._hovered else None
            foreground, icon_color, font = colors.text, colors.muted, FONT_REGULAR
        self.control.bgcolor = background
        self._icon.color = icon_color
        self._label.color = foreground
        self._label.font_family = font
        self._badge.bgcolor = colors.signal


class Sidebar:
    def __init__(self, on_select: Callable[[str], None]) -> None:
        self._items: dict[str, _NavItem] = {}
        tools = [self._add(key, label, icon, on_select) for key, label, icon in TOOL_ITEMS]
        app = [self._add(key, label, icon, on_select) for key, label, icon in APP_ITEMS]
        colors = palette()
        self.control = ft.Container(
            width=236,
            bgcolor=colors.background,
            padding=ft.Padding.symmetric(horizontal=14, vertical=22),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            brand_mark(34),
                            ft.Column(
                                [
                                    text("ADB Toolkit", size=15, font=FONT_SEMIBOLD),
                                    text(f"v{APP_VERSION}", size=12, mono=True, color=colors.muted),
                                ],
                                spacing=0,
                                tight=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=24),
                    *tools,
                    ft.Container(height=12),
                    hairline(),
                    ft.Container(height=12),
                    *app,
                ],
                spacing=4,
            ),
        )

    def _add(self, key: str, label: str, icon: str, on_select: Callable[[str], None]) -> ft.Container:
        item = _NavItem(key, label, icon, on_select)
        self._items[key] = item
        return item.control

    def select(self, key: str) -> None:
        for name, item in self._items.items():
            item.select(name == key)

    def set_update_badge(self, visible: bool) -> None:
        self._items["updates"].set_badge(visible)
