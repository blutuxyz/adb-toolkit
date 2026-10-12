"""Small building blocks shared by the screens. Screens build their controls from these, not from raw Flet widgets."""

import zlib

import flet as ft

from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    FONT_MONO,
    FONT_REGULAR,
    FONT_SEMIBOLD,
    ICON_INLINE,
    ICON_TILE,
    MEASURE_WIDTH,
    RADIUS_TILE,
    ROW_PADDING,
    SECTION_GAP,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XS,
    SPEC_LABEL_WIDTH,
    TYPE_BODY,
    TYPE_CAPTION,
    TYPE_DISPLAY,
    TYPE_LABEL,
    TYPE_TITLE,
    palette,
)

# The hues that letter tiles rotate through. Accent is left out: it means action, not an app.
_LETTER_HUES = ("blue", "green", "violet", "amber", "rose")


def text(value: str, *, size: float = TYPE_BODY, color: str | None = None, font: str = FONT_REGULAR,
         mono: bool = False, **kwargs) -> ft.Text:
    return ft.Text(
        value,
        size=size,
        color=color or palette().text,
        font_family=FONT_MONO if mono else font,
        **kwargs,
    )


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


def icon_tile(icon: str, hue: str = "accent", size: float = ICON_TILE) -> ft.Container:
    """A rounded square with a tint of the hue behind an icon of that hue. It heads empty states and dialogs."""
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


def letter_tile(package: str, size: float = 32) -> ft.Container:
    """Stands in for the app icon. Icons need the APK, which adb does not hand out."""
    color = hue_color(letter_hue(package))
    letter = (package.split(".")[-1][:1] or "?").upper()
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=ft.Colors.with_opacity(0.16, color),
        alignment=ft.Alignment.CENTER,
        content=text(letter, size=TYPE_LABEL, font=FONT_SEMIBOLD, color=color),
    )


_BUTTON_KINDS = ("filled", "outlined", "text", "text_danger", "danger")


def button(
    kind: str,
    label: str,
    *,
    icon: str | None = None,
    on_click=None,
    disabled: bool = False,
    visible: bool = True,
    height: float = CONTROL_HEIGHT,
) -> ft.Control:
    """Every button in the app. The kind says how much weight the action has on its screen.

    filled: the one main action of a screen or dialog. outlined: every other action.
    text: a quiet action such as Cancel. text_danger: a destructive action inside a row.
    danger: the confirm button of a destructive dialog.
    """
    if kind not in _BUTTON_KINDS:
        raise ValueError(f"unknown button kind: {kind}")
    colors = palette()
    shape = ft.RoundedRectangleBorder(radius=height / 2)
    # The label has no colour of its own, so it follows the button's state (disabled, pressed).
    content = ft.Text(label, size=TYPE_BODY, font_family=FONT_REGULAR)
    common = {"content": content, "icon": icon, "on_click": on_click, "disabled": disabled,
              "visible": visible, "height": height}
    if kind == "filled":
        return ft.FilledButton(style=ft.ButtonStyle(shape=shape), **common)
    if kind == "outlined":
        side = ft.BorderSide(1, colors.control_border)
        return ft.OutlinedButton(style=ft.ButtonStyle(shape=shape, side=side), **common)
    if kind == "text":
        return ft.TextButton(style=ft.ButtonStyle(shape=shape), **common)
    if kind == "text_danger":
        return ft.TextButton(style=ft.ButtonStyle(shape=shape, color=colors.danger), **common)
    return ft.FilledButton(
        style=ft.ButtonStyle(shape=shape, bgcolor=colors.danger, color=colors.on_danger),
        **common,
    )


def page_header(
    title: str,
    *,
    subtitle: str = "",
    hue: str = "accent",
    meta: str = "",
) -> ft.Row:
    """A screen's title. A bar in the area's hue stands in front of it, and mono metadata sits on the right."""
    bar = ft.Container(width=4, height=44 if subtitle else 32, border_radius=2, bgcolor=hue_color(hue))
    title_column = [
        ft.Text(title, size=TYPE_DISPLAY, font_family=FONT_SEMIBOLD, color=palette().text,
                style=ft.TextStyle(letter_spacing=-0.4)),
    ]
    if subtitle:
        title_column.append(text(subtitle, color=palette().muted))
    row: list[ft.Control] = [bar, ft.Column(title_column, spacing=SPACE_XS, tight=True)]
    if meta:
        row += [ft.Container(expand=True), text(meta, size=TYPE_CAPTION, mono=True, color=palette().muted)]
    return ft.Row(row, spacing=SPACE_M, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def screen_frame(
    title: str,
    body: ft.Control,
    *,
    subtitle: str = "",
    hue: str = "accent",
    meta: str = "",
    toolbar: ft.Control | None = None,
) -> ft.Column:
    """A screen: its header, an optional toolbar, then the body, which fills the rest and scrolls itself."""
    head: list[ft.Control] = [page_header(title, subtitle=subtitle, hue=hue, meta=meta)]
    if toolbar is not None:
        head.append(toolbar)
    return ft.Column(
        [ft.Column(head, spacing=SECTION_GAP, tight=True), ft.Container(expand=True, content=body)],
        expand=True,
        spacing=SECTION_GAP,
    )


def spec_section(
    title: str,
    children: list[ft.Control],
    *,
    description: str = "",
    action: ft.Control | None = None,
) -> ft.Row:
    """A two-column block: the section's name and description on the left, its rows on the right.

    The left column is what the section is for; the right column is what can be done in it.
    """
    left: list[ft.Control] = [text(title, size=TYPE_TITLE, font=FONT_SEMIBOLD)]
    if description:
        left.append(text(description, color=palette().muted))
    if action is not None:
        left.append(ft.Container(padding=ft.Padding.only(top=SPACE_S), content=action))
    return ft.Row(
        [
            ft.Container(width=SPEC_LABEL_WIDTH, content=ft.Column(left, spacing=SPACE_XS, tight=True)),
            ft.Column(children, spacing=0, expand=True, tight=True),
        ],
        spacing=SPACE_L,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def sections(*blocks: ft.Control) -> list[ft.Control]:
    """Stack spec sections with a full-width hairline between them."""
    out: list[ft.Control] = []
    for index, block in enumerate(blocks):
        if index:
            out.append(ft.Container(padding=ft.Padding.symmetric(vertical=SECTION_GAP / 2), content=hairline()))
        out.append(block)
    return out


class StatusLine:
    """A coloured lamp and a label. Its colours are set with `set`, which also sends them to the page."""

    def __init__(self, label: str = "", color: str | None = None) -> None:
        self._dot = status_dot(color or palette().muted, size=10)
        self._label = text(label, size=TYPE_LABEL, font=FONT_SEMIBOLD)
        self.control = ft.Row(
            [self._dot, self._label],
            spacing=SPACE_S,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def set(self, label: str, color: str) -> None:
        # A parent's update does not send a child's new colour, so the children are updated here.
        self._label.value = label
        self._dot.bgcolor = color
        self._dot.update()
        self._label.update()


def empty_state(
    title: str,
    body: str,
    *,
    icon: str = "",
    hue: str = "blue",
    spinner: bool = False,
    action: ft.Control | None = None,
) -> ft.Column:
    marker = ft.ProgressRing(width=24, height=24, stroke_width=2) if spinner else icon_tile(icon, hue, size=56)
    children: list[ft.Control] = [marker, text(title, size=TYPE_TITLE, font=FONT_SEMIBOLD)]
    if body:
        children.append(ft.Container(width=MEASURE_WIDTH, content=text(body, color=palette().muted)))
    if action is not None:
        children.append(action)
    return ft.Column(children, spacing=SPACE_M, tight=True)


def spec_row(
    title: str,
    description: str,
    action: ft.Control | None = None,
    *,
    icon: str | None = None,
    hue: str = "accent",
) -> ft.Container:
    """One row of a spec section: a small hue-coloured icon, the title and description, and the action."""
    leading: list[ft.Control] = []
    if icon:
        leading.append(ft.Icon(icon, size=ICON_INLINE, color=hue_color(hue)))
    trailing: list[ft.Control] = [action] if action is not None else []
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        content=ft.Row(
            [
                *leading,
                ft.Column(
                    [
                        text(title, size=TYPE_LABEL, font=FONT_SEMIBOLD),
                        text(description, color=palette().muted),
                    ],
                    spacing=SPACE_XS,
                    tight=True,
                    expand=True,
                ),
                *trailing,
            ],
            spacing=SPACE_M,
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
