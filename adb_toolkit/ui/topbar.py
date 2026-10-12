"""The device strip across the top: the selected phone, its state, and the buttons that connect and refresh."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.session import Session
from adb_toolkit.ui.theme import (
    FONT_SEMIBOLD,
    GUTTER,
    HEADER_CONTROL_HEIGHT,
    ICON_INLINE,
    RADIUS_CARD,
    SPACE_M,
    SPACE_S,
    TOPBAR_HEIGHT,
    TYPE_BODY,
    TYPE_CAPTION,
    TYPE_TITLE,
    palette,
)
from adb_toolkit.ui.widgets import button, device_state, ripple, status_dot, text

PICKER_WIDTH = 360  # the menu is at least this wide, so a long device name still has room
MENU_ROW_HEIGHT = 56  # two lines: the name, then the address and state

# One line each, cut with an ellipsis, so a long name never breaks the strip or the menu.
_ONE_LINE = {"no_wrap": True, "overflow": ft.TextOverflow.ELLIPSIS}


class TopBar:
    def __init__(
        self,
        on_pick: Callable[[str], None],
        on_connect: Callable[[], None],
        on_refresh: Callable[[], None],
    ) -> None:
        self._on_pick = on_pick
        colors = palette()
        self._picker = ft.PopupMenuButton(
            items=[],
            content=ft.Container(),
            padding=0,
            # Drop the menu under the strip. The default draws it over the device name.
            menu_position=ft.PopupMenuPosition.UNDER,
            menu_padding=ft.Padding.symmetric(vertical=SPACE_S),
            size_constraints=ft.BoxConstraints(min_width=PICKER_WIDTH),
            bgcolor=colors.panel,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        )
        self._connect = button(
            "outlined",
            "Connect over Wi-Fi",
            icon=ft.Icons.WIFI,
            height=HEADER_CONTROL_HEIGHT,
            on_click=lambda _: on_connect(),
        )
        self._refresh = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh devices",
            icon_color=colors.muted,
            width=HEADER_CONTROL_HEIGHT,
            height=HEADER_CONTROL_HEIGHT,
            on_click=lambda _: on_refresh(),
        )
        self.control = ft.Container(
            height=TOPBAR_HEIGHT,
            bgcolor=colors.bar,
            padding=ft.Padding.symmetric(horizontal=GUTTER),
            border=ft.Border.only(bottom=ft.BorderSide(1, colors.line)),
            content=ft.Row(
                [self._picker, ft.Container(expand=True), self._connect, self._refresh],
                spacing=SPACE_M,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def show(self, session: Session) -> None:
        """Redraw the device name and the menu for the current device list and selection."""
        selected = session.selected_device
        self._picker.content = _strip_name(selected, len(session.devices))
        self._picker.items = self._menu_items(session)
        self.control.update()

    def _menu_items(self, session: Session) -> list[ft.PopupMenuItem]:
        if not session.devices:
            return [
                ft.PopupMenuItem(
                    content=text("No devices connected", color=palette().muted),
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


def _strip_name(device: Device | None, count: int) -> ft.Container:
    """The selected phone, big: its name, then the serial and state in mono. Clicking it opens the list."""
    colors = palette()
    _, lamp_color = device_state(device)
    if device is None:
        title = "No device"
        subline = "Connect a phone" if count == 0 else "Choose a device"
    else:
        title, subline = _device_lines(device)
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=SPACE_S),
        border_radius=RADIUS_CARD,
        ink=True,
        ink_color=ripple(),
        content=ft.Row(
            [
                status_dot(lamp_color, size=10),
                ft.Column(
                    [
                        text(title, size=TYPE_TITLE, font=FONT_SEMIBOLD, **_ONE_LINE),
                        text(subline, size=TYPE_CAPTION, mono=True, color=colors.muted, **_ONE_LINE),
                    ],
                    spacing=0,
                    tight=True,
                ),
                ft.Icon(ft.Icons.UNFOLD_MORE, size=ICON_INLINE, color=colors.muted),
            ],
            spacing=SPACE_M,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _menu_row(device: Device) -> ft.Row:
    """One device in the picker menu, laid out like the strip: name on top, address and state below."""
    _, lamp_color = device_state(device)
    title, subline = _device_lines(device)
    return ft.Row(
        [
            status_dot(lamp_color, size=8),
            ft.Column(
                [
                    text(title, size=TYPE_BODY, font=FONT_SEMIBOLD, **_ONE_LINE),
                    text(subline, size=TYPE_CAPTION, mono=True, color=palette().muted, **_ONE_LINE),
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
