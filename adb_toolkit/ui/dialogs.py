"""Confirmation and connection dialogs."""

import re
from collections.abc import Callable

import flet as ft

from adb_toolkit.ui.theme import FONT_SEMIBOLD, palette
from adb_toolkit.ui.widgets import text

# host:port, for example 192.168.1.20:5555
_WIFI_ADDRESS = re.compile(r"^[\w.-]+:\d{2,5}$")


def confirm(
    page: ft.Page,
    *,
    title: str,
    message: str,
    action_label: str,
    on_confirm: Callable[[], None],
    destructive: bool = False,
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
            title=text(title, size=18, font=FONT_SEMIBOLD),
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
    )

    def submit(_=None) -> None:
        address = (field.value or "").strip()
        if not _WIFI_ADDRESS.match(address):
            field.error = "Use the IP address and port, for example 192.168.1.20:5555."
            page.update()
            return
        page.pop_dialog()
        on_connect(address)

    field.on_submit = submit
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=text("Connect over Wi-Fi", size=18, font=FONT_SEMIBOLD),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    [
                        text(
                            "On the phone, turn on Wireless debugging under Developer options. "
                            "Then enter the address it shows.",
                            color=colors.muted,
                        ),
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
