"""Top bar: the device picker, plus the buttons that connect and refresh."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.session import Session
from adb_toolkit.ui.theme import FONT_SEMIBOLD, GUTTER, HEADER_CONTROL_HEIGHT, RADIUS_CARD, palette
from adb_toolkit.ui.widgets import device_state, ripple, status_dot, text

PICKER_WIDTH = 340  # the chip and its menu share this width, so the menu lines up under the chip
MENU_ROW_HEIGHT = 56  # two lines: the name, then the address and state

# One line each, cut with an ellipsis, so a long name never breaks the chip or the menu.
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
            # Drop the menu under the chip. The default draws it over the chip.
            menu_position=ft.PopupMenuPosition.UNDER,
            menu_padding=ft.Padding.symmetric(vertical=8),
            size_constraints=ft.BoxConstraints(min_width=PICKER_WIDTH),
            bgcolor=colors.panel,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        )
        self._connect = ft.OutlinedButton(
            content=text("Connect over Wi-Fi"),
            icon=ft.Icons.WIFI,
            icon_color=colors.accent,
            height=HEADER_CONTROL_HEIGHT,
            on_click=lambda _: on_connect(),
        )
        self._refresh = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh devices",
            icon_color=colors.accent,
            width=HEADER_CONTROL_HEIGHT,
            height=HEADER_CONTROL_HEIGHT,
            on_click=lambda _: on_refresh(),
        )
        self.control = ft.Container(
            height=72,
            bgcolor=colors.bar,
            padding=ft.Padding.symmetric(horizontal=GUTTER),
            border=ft.Border.only(bottom=ft.BorderSide(1, colors.line)),
            content=ft.Row(
                [self._picker, self._connect, self._refresh],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def show(self, session: Session) -> None:
        """Redraw the picker for the current device list and selection."""
        selected = session.selected_device
        self._picker.content = _chip(selected, len(session.devices))
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


def _chip(device: Device | None, count: int) -> ft.Container:
    colors = palette()
    _, dot_color = device_state(device)
    if device is None:
        title = "No device"
        subline = "Connect a phone" if count == 0 else "Choose a device"
    else:
        title, subline = _device_lines(device)
    return ft.Container(
        width=PICKER_WIDTH,
        height=HEADER_CONTROL_HEIGHT,
        padding=ft.Padding.symmetric(horizontal=16),
        border_radius=HEADER_CONTROL_HEIGHT / 2,
        bgcolor=colors.panel,
        border=ft.Border.all(1, colors.line),
        ink=True,
        ink_color=ripple(),
        content=ft.Row(
            [
                status_dot(dot_color, size=9),
                ft.Column(
                    [
                        text(title, size=14, font=FONT_SEMIBOLD, **_ONE_LINE),
                        text(subline, size=12, mono=True, color=colors.muted, **_ONE_LINE),
                    ],
                    spacing=1,
                    tight=True,
                    expand=True,
                ),
                ft.Icon(ft.Icons.UNFOLD_MORE, size=18, color=colors.muted),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _menu_row(device: Device) -> ft.Row:
    """One device in the picker menu, laid out like the chip: name on top, address and state below."""
    _, dot_color = device_state(device)
    title, subline = _device_lines(device)
    return ft.Row(
        [
            status_dot(dot_color, size=8),
            ft.Column(
                [
                    text(title, size=14, font=FONT_SEMIBOLD, **_ONE_LINE),
                    text(subline, size=12, mono=True, color=palette().muted, **_ONE_LINE),
                ],
                spacing=1,
                tight=True,
                expand=True,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _device_lines(device: Device) -> tuple[str, str]:
    """The name and the second line for a device. The serial is only repeated when it is not the name."""
    label, _ = device_state(device)
    if device.title == device.serial:
        return device.title, label
    return device.title, f"{device.serial} · {label}"
