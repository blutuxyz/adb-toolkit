"""Top bar: the device picker, plus the buttons that connect and refresh."""

from collections.abc import Callable

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.session import Session
from adb_toolkit.ui.theme import FONT_SEMIBOLD, palette
from adb_toolkit.ui.widgets import device_state, status_dot, text


class TopBar:
    def __init__(
        self,
        on_pick: Callable[[str], None],
        on_connect: Callable[[], None],
        on_refresh: Callable[[], None],
    ) -> None:
        self._on_pick = on_pick
        colors = palette()
        self._picker = ft.PopupMenuButton(items=[], content=ft.Container())
        self._connect = ft.OutlinedButton(
            content=text("Connect over Wi-Fi"),
            icon=ft.Icons.WIFI,
            on_click=lambda _: on_connect(),
        )
        self._refresh = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh devices",
            icon_color=colors.muted,
            on_click=lambda _: on_refresh(),
        )
        self.control = ft.Container(
            height=72,
            bgcolor=colors.bar,
            padding=ft.Padding.symmetric(horizontal=20),
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
            return [ft.PopupMenuItem(content=text("No devices connected", color=palette().muted), disabled=True)]
        return [
            ft.PopupMenuItem(
                content=_menu_row(device),
                on_click=lambda _, serial=device.serial: self._on_pick(serial),
            )
            for device in session.devices
        ]


def _chip(device: Device | None, count: int) -> ft.Container:
    colors = palette()
    label, dot_color = device_state(device)
    if device is None:
        title = "No device"
        subline = "Plug in a phone or connect over Wi-Fi" if count == 0 else "Choose a device"
    else:
        title = device.title
        subline = label if device.title == device.serial else f"{device.serial} · {label}"
    return ft.Container(
        width=340,
        height=48,
        padding=ft.Padding.symmetric(horizontal=14),
        border_radius=12,
        bgcolor=colors.panel,
        border=ft.Border.all(1, colors.line),
        content=ft.Row(
            [
                status_dot(dot_color, size=9),
                ft.Column(
                    [
                        text(title, size=14, font=FONT_SEMIBOLD),
                        text(subline, size=12, mono=True, color=colors.muted),
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
    _, dot_color = device_state(device)
    controls: list[ft.Control] = [status_dot(dot_color, size=8), text(device.title, size=14)]
    if device.title != device.serial:
        controls.append(text(device.serial, size=12, mono=True, color=palette().muted))
    return ft.Row(controls, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
