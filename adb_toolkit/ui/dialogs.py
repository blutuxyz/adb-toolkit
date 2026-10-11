"""Confirmation and connection dialogs."""

import re
from collections.abc import Callable

import flet as ft

from adb_toolkit.ui.theme import CONTROL_HEIGHT, FONT_SEMIBOLD, RADIUS_CARD, palette
from adb_toolkit.ui.widgets import icon_tile, text

# host:port, for example 192.168.1.20:5555
_WIFI_ADDRESS = re.compile(r"^[\w.-]+:\d{2,5}$")


def _titled(icon: str, hue: str, title: str) -> ft.Row:
    """A dialog title with an icon tile in front of it."""
    return ft.Row(
        [icon_tile(icon, hue), text(title, size=18, font=FONT_SEMIBOLD)],
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def confirm(
    page: ft.Page,
    *,
    title: str,
    message: str,
    action_label: str,
    on_confirm: Callable[[], None],
    destructive: bool = False,
    icon: str = ft.Icons.INFO_OUTLINE,
    hue: str = "accent",
) -> None:
    colors = palette()

    def close(_=None) -> None:
        page.pop_dialog()

    def accept(_) -> None:
        page.pop_dialog()
        on_confirm()

    action_color = colors.danger if destructive else colors.accent
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
            title=_titled(icon, hue, title),
            content=ft.Container(width=440, content=text(message, color=colors.muted)),
            actions=[
                ft.TextButton(content=text("Cancel"), on_click=close),
                ft.FilledButton(
                    content=text(action_label, color=colors.background if destructive else colors.on_accent),
                    style=ft.ButtonStyle(bgcolor=action_color),
                    on_click=accept,
                ),
            ],
        )
    )


def show_connect_wifi_dialog(page: ft.Page, on_connect: Callable[[str], None]) -> None:
    colors = palette()
    field = ft.TextField(
        label="Address",
        hint_text="192.168.1.20:5555",
        width=420,
        autofocus=True,
        height=CONTROL_HEIGHT,
        border_radius=CONTROL_HEIGHT / 2,
        border_color=colors.line,
        focused_border_color=colors.accent,
        cursor_color=colors.accent,
    )

    def submit(_=None) -> None:
        address = (field.value or "").strip()
        if not _WIFI_ADDRESS.match(address):
            field.error_text = "Enter an address like 192.168.1.20:5555."
            page.update()
            return
        page.pop_dialog()
        on_connect(address)

    field.on_submit = submit
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
            title=_titled(ft.Icons.WIFI, "accent", "Connect over Wi-Fi"),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    [
                        text("Enter the address shown under Wireless debugging.", color=colors.muted),
                        field,
                    ],
                    spacing=16,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton(content=text("Cancel"), on_click=lambda _: page.pop_dialog()),
                ft.FilledButton(content=text("Connect", color=colors.on_accent), on_click=submit),
            ],
        )
    )
