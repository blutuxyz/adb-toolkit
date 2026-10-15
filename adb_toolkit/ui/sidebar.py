"""The sidebar: the brand, the device picker, then the screens in two labelled groups.

The picker shows the selected phone at the top, so the device is always in view. Each screen
keeps its identity hue on its icon.
"""

from collections.abc import Callable

import flet as ft

from adb_toolkit.config import APP_VERSION
from adb_toolkit.core.devices import Device
from adb_toolkit.core.session import Session
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    ICON_INLINE,
    ICON_NAV,
    MOTION_STATE_MS,
    RADIUS_CARD,
    RADIUS_CONTROL,
    SIDEBAR_WIDTH,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XS,
    TYPE_BODY,
    TYPE_CAPTION,
    TYPE_LABEL,
    TYPE_TITLE,
    palette,
)
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.widgets import ONE_LINE, brand_mark, button, device_state, hue_color, ripple, status_dot, text

PICKER_WIDTH = 320  # the menu is at least this wide, so a long device name still has room
MENU_ROW_HEIGHT = 56  # two lines: the name, then the address and state

# key, label, icon, hue. Labels are short; the group heading says what the screens are for.
TOOL_ITEMS = (
    ("apps", "Apps", ft.Icons.APPS_OUTLINED, "blue"),
    ("adb", "ADB Tools", ft.Icons.TERMINAL, "green"),
    ("fastboot", "Fastboot", ft.Icons.FLASH_ON_OUTLINED, "violet"),
    ("files", "Files", ft.Icons.FOLDER_OPEN_OUTLINED, "amber"),
    ("capture", "Capture", ft.Icons.PHOTO_CAMERA_OUTLINED, "rose"),
    ("console", "Console", ft.Icons.CODE, "blue"),
)
APP_ITEMS = (
    ("settings", "Settings", ft.Icons.SETTINGS_OUTLINED, "amber"),
    ("updates", "Updates", ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED, "accent"),
    ("about", "About", ft.Icons.INFO_OUTLINE, "rose"),
)


class _NavItem:
    def __init__(self, key: str, label: str, icon: str, hue: str, on_select: Callable[[str], None]) -> None:
        self.key = key
        self._hue = hue
        self._selected = False
        self._hovered = False
        self._icon = ft.Icon(icon, size=ICON_NAV)
        self._label = text(t(label), size=TYPE_BODY)
        # The dot says an update is waiting. It is hidden unless set.
        self._lamp = status_dot(palette().signal, size=8)
        self._lamp.visible = False
        self.control = ft.Container(
            height=CONTROL_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=SPACE_M),
            border_radius=RADIUS_CONTROL,
            ink=True,
            ink_color=ripple(),
            animate=ft.Animation(MOTION_STATE_MS, ft.AnimationCurve.EASE_OUT),
            on_click=lambda _: on_select(key),
            on_hover=self._on_hover,
            content=ft.Row(
                [self._icon, self._label, ft.Container(expand=True), self._lamp],
                spacing=SPACE_M,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
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
        for control in (self.control, self._icon, self._label, self._lamp):
            control.update()

    def _paint(self) -> None:
        colors = palette()
        self._icon.color = hue_color(self._hue)
        self._lamp.bgcolor = colors.signal
        if self._selected:
            self.control.bgcolor = colors.accent_soft
            self._label.color = colors.on_accent_soft
            self._label.weight = ft.FontWeight.W_600
        else:
            # Transparent at zero opacity, so the fade does not pass through black.
            self.control.bgcolor = colors.panel_high if self._hovered else ft.Colors.with_opacity(0, colors.bar)
            self._label.color = colors.muted
            self._label.weight = None


class Sidebar:
    def __init__(
        self,
        *,
        on_select: Callable[[str], None],
        on_pick: Callable[[str], None],
        on_connect: Callable[[], None],
        on_refresh: Callable[[], None],
    ) -> None:
        colors = palette()
        self._on_pick = on_pick
        self._items: dict[str, _NavItem] = {}

        self._lamp = status_dot(colors.muted, size=10)
        self._title = text("", size=TYPE_LABEL, strong=True, **ONE_LINE)
        self._subline = text("", size=TYPE_CAPTION, mono=True, color=colors.muted, **ONE_LINE)
        device_card = ft.Container(
            padding=ft.Padding.all(SPACE_M),
            border_radius=RADIUS_CARD,
            bgcolor=colors.background,
            border=ft.Border.all(1, colors.line),
            content=ft.Row(
                [
                    self._lamp,
                    ft.Column([self._title, self._subline], spacing=SPACE_XS, tight=True, expand=True),
                    ft.Icon(ft.Icons.UNFOLD_MORE, size=ICON_INLINE, color=colors.muted),
                ],
                spacing=SPACE_M,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self._picker = ft.PopupMenuButton(
            items=[],
            content=device_card,
            padding=0,
            # Drop the menu under the card. The default draws it over the device name.
            menu_position=ft.PopupMenuPosition.UNDER,
            menu_padding=ft.Padding.symmetric(vertical=SPACE_S),
            size_constraints=ft.BoxConstraints(min_width=PICKER_WIDTH),
            bgcolor=colors.panel,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        )
        connect = button(
            "outlined",
            t("Connect Wi-Fi"),
            icon=ft.Icons.WIFI,
            on_click=lambda _: on_connect(),
        )
        refresh = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip=t("Refresh devices"),
            icon_color=colors.muted,
            on_click=lambda _: on_refresh(),
        )

        tools = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in TOOL_ITEMS]
        apps = [self._add(key, label, icon, hue, on_select) for key, label, icon, hue in APP_ITEMS]
        self.control = ft.Container(
            width=SIDEBAR_WIDTH,
            bgcolor=colors.bar,
            border=ft.Border.only(right=ft.BorderSide(1, colors.line)),
            padding=ft.Padding.symmetric(vertical=SPACE_L),
            content=ft.Column(
                [
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=SPACE_L),
                        content=ft.Row(
                            [
                                brand_mark(36),
                                ft.Column(
                                    [
                                        text("ADB Toolkit", size=TYPE_TITLE, strong=True),
                                        text(f"v{APP_VERSION}", size=TYPE_CAPTION, mono=True, color=colors.muted),
                                    ],
                                    spacing=0,
                                    tight=True,
                                ),
                            ],
                            spacing=SPACE_M,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=SPACE_M, vertical=SPACE_L),
                        content=ft.Column(
                            [
                                self._picker,
                                ft.Row(
                                    [ft.Container(expand=True, content=connect), refresh],
                                    spacing=SPACE_XS,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=SPACE_S,
                            tight=True,
                        ),
                    ),
                    _group_label(t("Tools")),
                    ft.Container(padding=ft.Padding.symmetric(horizontal=SPACE_M), content=ft.Column(tools, spacing=SPACE_XS, tight=True)),
                    ft.Container(height=SPACE_L),
                    _group_label(t("App")),
                    ft.Container(padding=ft.Padding.symmetric(horizontal=SPACE_M), content=ft.Column(apps, spacing=SPACE_XS, tight=True)),
                ],
                spacing=0,
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

    def show_device(self, session: Session) -> None:
        """Redraw the selected phone and the picker's list for the current devices and selection."""
        selected = session.selected_device
        _, lamp_color = device_state(selected)
        if selected is None:
            title = t("No device")
            subline = t("Connect a phone") if not session.devices else t("Choose a device")
        else:
            title, subline = _device_lines(selected)
        self._lamp.bgcolor = lamp_color
        self._title.value = title
        self._subline.value = subline
        self._picker.items = self._menu_items(session)
        for control in (self._lamp, self._title, self._subline, self._picker):
            control.update()

    def _menu_items(self, session: Session) -> list[ft.PopupMenuItem]:
        if not session.devices:
            return [
                ft.PopupMenuItem(
                    content=text(t("No devices connected"), color=palette().muted),
                    height=MENU_ROW_HEIGHT,
                    disabled=True,
                )
            ]
        return [
            ft.PopupMenuItem(
                content=_menu_row(device),
                height=MENU_ROW_HEIGHT,
                checked=device.serial == session.selected_serial,
                on_click=lambda _, serial=device.serial: self._on_pick(serial),
            )
            for device in session.devices
        ]


def _group_label(label: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding.only(left=SPACE_L, right=SPACE_L, bottom=SPACE_XS),
        content=text(label.upper(), size=TYPE_CAPTION, strong=True, color=palette().muted, style=ft.TextStyle(letter_spacing=0.8)),
    )


def _menu_row(device: Device) -> ft.Row:
    """One device in the picker menu: its lamp, then the name on top and address and state below."""
    _, lamp_color = device_state(device)
    title, subline = _device_lines(device)
    return ft.Row(
        [
            status_dot(lamp_color, size=8),
            ft.Column(
                [
                    text(title, size=TYPE_BODY, strong=True, **ONE_LINE),
                    text(subline, size=TYPE_CAPTION, mono=True, color=palette().muted, **ONE_LINE),
                ],
                spacing=0,
                tight=True,
                expand=True,
            ),
        ],
        spacing=SPACE_M,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _device_lines(device: Device) -> tuple[str, str]:
    """The name and the second line for a device. The serial is only repeated when it is not the name."""
    label, _ = device_state(device)
    if device.title == device.serial:
        return device.title, label
    return device.title, f"{device.serial} · {label}"
