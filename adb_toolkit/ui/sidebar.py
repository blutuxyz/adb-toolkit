"""Left navigation: the tool groups first, then settings and information."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.config import APP_VERSION
from adb_toolkit.ui.theme import CONTROL_HEIGHT, FONT_REGULAR, FONT_SEMIBOLD, MOTION_STATE_MS, palette
from adb_toolkit.ui.widgets import brand_mark, hairline, hue_color, ripple, text

# key, label, icon, hue. The hue is the area's identity colour, shown on its icon.
TOOL_ITEMS = (
    ("apps", "Apps", ft.Icons.APPS, "blue"),
    ("adb", "ADB Tools", ft.Icons.TERMINAL, "green"),
    ("fastboot", "Fastboot Tools", ft.Icons.FLASH_ON, "violet"),
)
APP_ITEMS = (
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED, "amber"),
    ("updates", "Updates", ft.Icons.SYSTEM_UPDATE_ALT, "accent"),
    ("about", "About", ft.Icons.INFO_OUTLINE, "rose"),
)


class _NavItem:
    def __init__(self, key: str, label: str, icon: str, hue: str, on_select: Callable[[str], None]) -> None:
        self.key = key
        self._hue = hue
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
            height=CONTROL_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=12),
            border_radius=CONTROL_HEIGHT / 2,
            ink=True,
            ink_color=ripple(),
            animate=ft.Animation(MOTION_STATE_MS, ft.AnimationCurve.EASE_OUT),
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
        # The icon keeps its hue in every state, so each area stays recognisable.
        self._icon.color = hue_color(self._hue)
        if self._selected:
            self.control.bgcolor = colors.accent_soft
            self._label.color = colors.on_accent_soft
            self._label.font_family = FONT_SEMIBOLD
        else:
            # Transparent rather than None, so the background can fade in and out.
            self.control.bgcolor = colors.panel_high if self._hovered else ft.Colors.TRANSPARENT
            self._label.color = colors.text
            self._label.font_family = FONT_REGULAR
        self._badge.bgcolor = colors.signal


class Sidebar:
    def __init__(self, on_select: Callable[[str], None]) -> None:
        self._items: dict[str, _NavItem] = {}
        tools = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in TOOL_ITEMS]
        app = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in APP_ITEMS]
        colors = palette()
        self.control = ft.Container(
            width=236,
            # A surface one step above the content, so the navigation reads as its own layer.
            bgcolor=colors.bar,
            padding=ft.Padding.symmetric(horizontal=16, vertical=24),
            content=ft.Column(
                [
                    # Same inset as a navigation item, so the brand mark lines up with the icons.
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12),
                        content=ft.Row(
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

    def _add(
        self, key: str, label: str, icon: str, hue: str, on_select: Callable[[str], None]
    ) -> ft.Container:
        item = _NavItem(key, label, icon, hue, on_select)
        self._items[key] = item
        return item.control

    def select(self, key: str) -> None:
        for name, item in self._items.items():
            item.select(name == key)

    def set_update_badge(self, visible: bool) -> None:
        self._items["updates"].set_badge(visible)
