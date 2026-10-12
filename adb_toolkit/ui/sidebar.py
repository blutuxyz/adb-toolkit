"""The icon rail: the tool areas first, then settings and information. Each area keeps its hue on its icon."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.ui.theme import (
    FONT_REGULAR,
    FONT_SEMIBOLD,
    ICON_NAV,
    MOTION_STATE_MS,
    RADIUS_CARD,
    SIDEBAR_WIDTH,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XS,
    TYPE_CAPTION,
    palette,
)
from adb_toolkit.ui.widgets import brand_mark, hairline, hue_color, ripple, text

# key, label, icon, hue. Labels are short because each one sits under its icon in a narrow rail.
TOOL_ITEMS = (
    ("apps", "Apps", ft.Icons.APPS_OUTLINED, "blue"),
    ("adb", "ADB", ft.Icons.TERMINAL, "green"),
    ("fastboot", "Fastboot", ft.Icons.FLASH_ON_OUTLINED, "violet"),
)
APP_ITEMS = (
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED, "amber"),
    ("updates", "Updates", ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED, "accent"),
    ("about", "About", ft.Icons.INFO_OUTLINE, "rose"),
)

_TILE = 40


class _RailItem:
    def __init__(self, key: str, label: str, icon: str, hue: str, on_select: Callable[[str], None]) -> None:
        self.key = key
        self._hue = hue
        self._selected = False
        self._hovered = False
        self._icon = ft.Icon(icon, size=ICON_NAV)
        self._tile = ft.Container(
            width=_TILE,
            height=_TILE,
            border_radius=RADIUS_CARD,
            alignment=ft.Alignment.CENTER,
            content=self._icon,
            animate=ft.Animation(MOTION_STATE_MS, ft.AnimationCurve.EASE_OUT),
        )
        # The lamp in the tile's corner says an update is waiting. It is hidden unless set.
        self._lamp = ft.Container(
            width=8,
            height=8,
            border_radius=4,
            visible=False,
            left=_TILE - 8,
            top=0,
        )
        self._label = text(label, size=TYPE_CAPTION, font=FONT_REGULAR)
        self.control = ft.Container(
            content=ft.Column(
                [
                    ft.Stack([self._tile, self._lamp], width=_TILE, height=_TILE),
                    self._label,
                ],
                spacing=SPACE_XS,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            width=SIDEBAR_WIDTH - 2 * SPACE_S,
            padding=ft.Padding.symmetric(vertical=SPACE_S),
            border_radius=RADIUS_CARD,
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
        self._lamp.visible = visible
        self._repaint()

    def _on_hover(self, event: ft.HoverEvent) -> None:
        self._hovered = str(event.data).lower() == "true"
        self._repaint()

    def _repaint(self) -> None:
        # Flet sends a child's new colour only when the child itself is updated.
        self._paint()
        for control in (self.control, self._tile, self._icon, self._lamp, self._label):
            control.update()

    def _paint(self) -> None:
        colors = palette()
        hue = hue_color(self._hue)
        self._icon.color = hue
        if self._selected:
            # The selected area fills its tile with its own hue, so the rail shows where you are by colour.
            self._tile.bgcolor = ft.Colors.with_opacity(0.22, hue)
            self._tile.border = ft.Border.all(1, hue)
            self._label.color = colors.text
            self._label.font_family = FONT_SEMIBOLD
        else:
            # Transparent at zero opacity of the same colour, so the fade does not pass through black.
            self._tile.bgcolor = colors.panel_high if self._hovered else ft.Colors.with_opacity(0, hue)
            self._tile.border = ft.Border.all(1, ft.Colors.with_opacity(0, hue))
            self._label.color = colors.muted
            self._label.font_family = FONT_REGULAR
        self._lamp.bgcolor = colors.signal


class Sidebar:
    def __init__(self, on_select: Callable[[str], None]) -> None:
        self._items: dict[str, _RailItem] = {}
        tools = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in TOOL_ITEMS]
        app = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in APP_ITEMS]
        colors = palette()
        self.control = ft.Container(
            width=SIDEBAR_WIDTH,
            bgcolor=colors.bar,
            padding=ft.Padding.symmetric(vertical=SPACE_L),
            content=ft.Column(
                [
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.only(bottom=SPACE_M),
                        content=brand_mark(40),
                    ),
                    *tools,
                    ft.Container(padding=ft.Padding.symmetric(vertical=SPACE_S), content=hairline()),
                    *app,
                ],
                spacing=SPACE_XS,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _add(
        self, key: str, label: str, icon: str, hue: str, on_select: Callable[[str], None]
    ) -> ft.Container:
        item = _RailItem(key, label, icon, hue, on_select)
        self._items[key] = item
        return item.control

    def select(self, key: str) -> None:
        for name, item in self._items.items():
            item.select(name == key)

    def set_update_badge(self, visible: bool) -> None:
        self._items["updates"].set_badge(visible)
