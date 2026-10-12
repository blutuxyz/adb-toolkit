"""Confirmation and connection dialogs. Both are built by `dialog_frame`, so they share one layout."""

import re
from collections.abc import Callable

import flet as ft

from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    FONT_SEMIBOLD,
    MEASURE_WIDTH,
    RADIUS_CARD,
    SPACE_L,
    TYPE_TITLE,
    palette,
)
from adb_toolkit.ui.widgets import button, icon_tile, text

# host:port, for example 192.168.1.20:5555
_WIFI_ADDRESS = re.compile(r"^[\w.-]+:\d{2,5}$")


def dialog_frame(
    *,
    icon: str,
    hue: str,
    title: str,
    body: list[ft.Control],
    actions: list[ft.Control],
) -> ft.AlertDialog:
    """A modal dialog: an icon tile and title, the body at the standard measure, and the buttons."""
    return ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        title=ft.Row(
            [icon_tile(icon, hue), text(title, size=TYPE_TITLE, font=FONT_SEMIBOLD)],
            spacing=SPACE_L,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        content=ft.Container(
            width=MEASURE_WIDTH,
            content=ft.Column(body, spacing=SPACE_L, tight=True),
        ),
        actions=actions,
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
    def close(_=None) -> None:
        page.pop_dialog()

    def accept(_) -> None:
        page.pop_dialog()
        on_confirm()

    page.show_dialog(
        dialog_frame(
            icon=icon,
            hue=hue,
            title=title,
            body=[text(message, color=palette().muted)],
            actions=[
                button("text", "Cancel", on_click=close),
                button("danger" if destructive else "filled", action_label, on_click=accept),
            ],
        )
    )


def show_connect_wifi_dialog(page: ft.Page, on_connect: Callable[[str], None]) -> None:
    colors = palette()
    field = ft.TextField(
        label="Address",
        hint_text="192.168.1.20:5555",
        width=MEASURE_WIDTH,
        autofocus=True,
        height=CONTROL_HEIGHT,
        border_radius=CONTROL_HEIGHT / 2,
        border_color=colors.control_border,
        focused_border_color=colors.accent,
        cursor_color=colors.accent,
    )

    def submit(_=None) -> None:
        address = (field.value or "").strip()
        if not _WIFI_ADDRESS.match(address):
            field.error = "Enter an address like 192.168.1.20:5555."
            page.update()
            return
        page.pop_dialog()
        on_connect(address)

    field.on_submit = submit
    page.show_dialog(
        dialog_frame(
            icon=ft.Icons.WIFI,
            hue="accent",
            title="Connect over Wi-Fi",
            body=[text("Enter the address shown under Wireless debugging.", color=colors.muted), field],
            actions=[
                button("text", "Cancel", on_click=lambda _: page.pop_dialog()),
                button("filled", "Connect", on_click=submit),
            ],
        )
    )
