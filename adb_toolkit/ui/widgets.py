"""Small building blocks shared by the screens."""

import zlib

import flet as ft

from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.ui.theme import (
    FONT_MONO,
    FONT_REGULAR,
    FONT_SEMIBOLD,
    RADIUS_TILE,
    ROW_PADDING,
    palette,
)

# The hues that letter tiles rotate through. The accent is included so the list is not one colour family.
_LETTER_HUES = ("blue", "green", "violet", "amber", "rose", "accent")


def text(value: str, *, size: float = 14, color: str | None = None, font: str = FONT_REGULAR,
         mono: bool = False, **kwargs) -> ft.Text:
    return ft.Text(
        value,
        size=size,
        color=color or palette().text,
        font_family=FONT_MONO if mono else font,
        **kwargs,
    )


def title_block(title: str) -> ft.Text:
    return text(title, size=26, font=FONT_SEMIBOLD)


def hairline() -> ft.Divider:
    return ft.Divider(height=1, thickness=1, color=palette().line)


def ripple() -> str:
    """Splash colour for a pressable container. It is the text colour, faint, so it reads in both themes."""
    return ft.Colors.with_opacity(0.14, palette().text)


def hue_color(name: str) -> str:
    """The colour for a named hue. 'accent' and 'danger' work too, so tiles can use them."""
    return getattr(palette(), name)


def status_dot(color: str, size: float = 9) -> ft.Container:
    return ft.Container(width=size, height=size, border_radius=size / 2, bgcolor=color)


def brand_mark(size: float = 32) -> ft.Container:
    """The 'adb' tile used as the app icon inside the window."""
    colors = palette()
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=colors.accent,
        alignment=ft.Alignment.CENTER,
        content=text("adb", size=size * 0.34, color=colors.on_accent, mono=True, font=FONT_SEMIBOLD),
    )


def icon_tile(icon: str, hue: str = "accent", size: float = 40) -> ft.Container:
    """A rounded square with a tint of the hue behind an icon of that hue. It heads rows, dialogs and empty states."""
    color = hue_color(hue)
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=ft.Colors.with_opacity(0.16, color),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon, size=size * 0.5, color=color),
    )


def letter_hue(package: str) -> str:
    """A stable hue for a package, so an app keeps its colour from one visit to the next."""
    return _LETTER_HUES[zlib.crc32(package.encode("utf-8")) % len(_LETTER_HUES)]


def letter_tile(package: str, size: float = 36) -> ft.Container:
    """Stands in for the app icon. Icons need the APK, which adb does not hand out."""
    color = hue_color(letter_hue(package))
    letter = (package.split(".")[-1][:1] or "?").upper()
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=ft.Colors.with_opacity(0.16, color),
        alignment=ft.Alignment.CENTER,
        content=text(letter, size=15, font=FONT_SEMIBOLD, color=color),
    )


def empty_state(title: str, body: str, *, icon: str = "", hue: str = "blue", spinner: bool = False) -> ft.Column:
    marker = ft.ProgressRing(width=24, height=24, stroke_width=2) if spinner else icon_tile(icon, hue, size=56)
    children: list[ft.Control] = [marker, text(title, size=18, font=FONT_SEMIBOLD)]
    if body:
        children.append(ft.Container(width=440, content=text(body, color=palette().muted)))
    return ft.Column(children, spacing=12, tight=True)


def action_row(
    title: str,
    description: str,
    action: ft.Control,
    *,
    icon: str | None = None,
    hue: str = "accent",
) -> ft.Container:
    """One line of a tool list: an optional icon tile, a title and description, and a button on the right."""
    leading: list[ft.Control] = [icon_tile(icon, hue)] if icon else []
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        content=ft.Row(
            [
                *leading,
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
            spacing=16,
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
