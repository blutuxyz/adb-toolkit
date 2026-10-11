"""Small building blocks shared by the screens."""

import flet as ft

from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.ui.theme import FONT_MONO, FONT_REGULAR, FONT_SEMIBOLD, palette


def text(value: str, *, size: float = 14, color: str | None = None, font: str = FONT_REGULAR,
         mono: bool = False, **kwargs) -> ft.Text:
    return ft.Text(
        value,
        size=size,
        color=color or palette().text,
        font_family=FONT_MONO if mono else font,
        **kwargs,
    )


def title_block(title: str, subtitle: str = "") -> ft.Column:
    children = [text(title, size=26, font=FONT_SEMIBOLD)]
    if subtitle:
        children.append(text(subtitle, color=palette().muted))
    return ft.Column(children, spacing=6, tight=True)


def hairline() -> ft.Divider:
    return ft.Divider(height=1, thickness=1, color=palette().line)


def status_dot(color: str, size: float = 9) -> ft.Container:
    return ft.Container(width=size, height=size, border_radius=size / 2, bgcolor=color)


def brand_mark(size: float = 32) -> ft.Container:
    """The 'adb' tile used as the app icon inside the window."""
    colors = palette()
    return ft.Container(
        width=size,
        height=size,
        border_radius=size * 0.28,
        bgcolor=colors.accent,
        alignment=ft.Alignment.CENTER,
        content=text("adb", size=size * 0.34, color=colors.on_accent, mono=True, font=FONT_SEMIBOLD),
    )


def empty_state(title: str, body: str, *, icon: str = "", spinner: bool = False) -> ft.Column:
    colors = palette()
    marker = ft.ProgressRing(width=24, height=24, stroke_width=2) if spinner else ft.Icon(icon, size=32, color=colors.muted)
    return ft.Column(
        [
            marker,
            text(title, size=17, font=FONT_SEMIBOLD),
            ft.Container(
                width=440,
                content=text(body, color=colors.muted),
            ),
        ],
        spacing=8,
        tight=True,
    )


def action_row(title: str, description: str, action: ft.Control) -> ft.Container:
    """One line of a tool list: a title and description on the left, a button on the right."""
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=18),
        content=ft.Row(
            [
                ft.Column(
                    [
                        text(title, size=15, font=FONT_SEMIBOLD),
                        text(description, color=palette().muted),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
                action,
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def device_state(device: Device | None) -> tuple[str, str]:
    """Human label and status colour for the device the user has selected."""
    colors = palette()
    if device is None:
        return "No device selected", colors.muted
    if device.is_ready:
        transport = _transport_label(device)
        return (f"Ready · {transport}" if transport else "Ready"), colors.accent
    if device.mode == FASTBOOT:
        return "Fastboot mode", colors.signal
    labels = {
        "unauthorized": "Unauthorized",
        "offline": "Offline",
        "no permissions": "No permissions",
        "recovery": "Recovery",
        "sideload": "Sideload",
    }
    label = labels.get(device.state, device.state.capitalize())
    if device.state in ("offline", "no permissions"):
        return label, colors.danger
    return label, colors.signal


def _transport_label(device: Device) -> str:
    return {"usb": "USB", "network": "Wi-Fi"}.get(device.transport, "")
