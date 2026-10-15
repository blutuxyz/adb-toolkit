"""Small building blocks shared by the screens. Screens build their controls from these, not from raw Flet widgets."""

import zlib
from collections.abc import Callable

import flet as ft

from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.core.process import percent_of
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CARD_PADDING,
    CONTROL_HEIGHT,
    FONT_MONO,
    ICON_ROW,
    ICON_TILE,
    MEASURE_WIDTH,
    RADIUS_CARD,
    RADIUS_CONTROL,
    RADIUS_PILL,
    RADIUS_TILE,
    ROW_PADDING,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XL,
    SPACE_XS,
    TYPE_BODY,
    TYPE_CAPTION,
    TYPE_DISPLAY,
    TYPE_LABEL,
    TYPE_TITLE,
    palette,
    text_scale,
)

# The hues that package tiles rotate through. Accent is left out: it means action, not an app.
_LETTER_HUES = ("blue", "green", "violet", "amber", "rose")

# One line each, cut with an ellipsis, so a long name never breaks a row.
ONE_LINE = {"no_wrap": True, "overflow": ft.TextOverflow.ELLIPSIS}


def text(value: str, *, size: float = TYPE_BODY, color: str | None = None, strong: bool = False,
         mono: bool = False, **kwargs) -> ft.Text:
    return ft.Text(
        value,
        size=size * text_scale(),
        color=color or palette().text,
        font_family=FONT_MONO if mono else None,
        weight=ft.FontWeight.W_600 if strong else None,
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


def status_dot(color: str, size: float = 8) -> ft.Container:
    return ft.Container(width=size, height=size, border_radius=size / 2, bgcolor=color)


def brand_mark(size: float = 32) -> ft.Container:
    """The app's mark: a teal tile with a terminal prompt in it."""
    colors = palette()
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=colors.accent,
        alignment=ft.Alignment.CENTER,
        content=text(">_", size=size * 0.36, color=colors.on_accent, mono=True, strong=True),
    )


def icon_tile(icon: str, hue: str = "accent", size: float = ICON_TILE) -> ft.Container:
    """A rounded square tinted with the hue, holding an icon of that hue."""
    color = hue_color(hue)
    return ft.Container(
        width=size,
        height=size,
        border_radius=RADIUS_TILE,
        bgcolor=ft.Colors.with_opacity(0.14, color),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon, size=size * 0.5, color=color),
    )


def letter_hue(package: str) -> str:
    """A stable hue for a package, so an app keeps its colour from one visit to the next."""
    return _LETTER_HUES[zlib.crc32(package.encode("utf-8")) % len(_LETTER_HUES)]


def tag(label: str, color: str) -> ft.Container:
    """A small pill that names a state. The label is set in the colour, on a faint tint of it."""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=SPACE_S, vertical=SPACE_XS),
        border_radius=RADIUS_PILL,
        bgcolor=ft.Colors.with_opacity(0.14, color),
        content=text(label, size=TYPE_CAPTION, color=color, strong=True),
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
    shape = ft.RoundedRectangleBorder(radius=RADIUS_CONTROL)
    # The colours are set here, not left to the theme, so every button reads from the palette.
    # The label has no colour of its own, so it follows the style for each state (disabled, pressed).
    content = ft.Text(label, size=TYPE_BODY * text_scale(), weight=ft.FontWeight.W_600, no_wrap=True)
    common = {"content": content, "icon": icon, "on_click": on_click, "disabled": disabled,
              "visible": visible, "height": height}
    if kind == "filled":
        style = ft.ButtonStyle(
            shape=shape,
            bgcolor=_by_state(colors.accent, colors.panel_high),
            color=_by_state(colors.on_accent, colors.muted),
        )
        return ft.FilledButton(style=style, **common)
    if kind == "outlined":
        style = ft.ButtonStyle(
            shape=shape,
            color=_by_state(colors.accent, colors.muted),
            side=_by_state(ft.BorderSide(1, colors.control_border), ft.BorderSide(1, colors.line)),
        )
        return ft.OutlinedButton(style=style, **common)
    if kind == "text":
        style = ft.ButtonStyle(shape=shape, color=_by_state(colors.text, colors.muted))
        return ft.TextButton(style=style, **common)
    if kind == "text_danger":
        style = ft.ButtonStyle(shape=shape, color=_by_state(colors.danger, colors.muted))
        return ft.TextButton(style=style, **common)
    style = ft.ButtonStyle(
        shape=shape,
        bgcolor=_by_state(colors.danger, colors.panel_high),
        color=_by_state(colors.on_danger, colors.muted),
    )
    return ft.FilledButton(style=style, **common)


def _by_state(enabled, disabled):
    """A button style value for each state: the value when it can be pressed, and the other when it cannot."""
    return {ft.ControlState.DEFAULT: enabled, ft.ControlState.DISABLED: disabled}


def page_header(
    title: str,
    *,
    subtitle: str = "",
    icon: str = "",
    hue: str = "accent",
    actions: list[ft.Control] | tuple[ft.Control, ...] = (),
) -> ft.Row:
    """A screen's title: its icon tile, the title and subtitle, and the screen's actions on the right."""
    row: list[ft.Control] = []
    if icon:
        row.append(icon_tile(icon, hue))
    title_column: list[ft.Control] = [
        text(title, size=TYPE_DISPLAY, strong=True, style=ft.TextStyle(letter_spacing=-0.3)),
    ]
    if subtitle:
        title_column.append(text(subtitle, color=palette().muted))
    row.append(ft.Column(title_column, spacing=SPACE_XS, tight=True, expand=True))
    row.extend(actions)
    return ft.Row(row, spacing=SPACE_L, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def screen_frame(
    title: str,
    body: ft.Control,
    *,
    subtitle: str = "",
    icon: str = "",
    hue: str = "accent",
    actions: list[ft.Control] | tuple[ft.Control, ...] = (),
    toolbar: ft.Control | None = None,
) -> ft.Column:
    """A screen: its header, an optional toolbar, then the body, which fills the rest and scrolls itself."""
    head: list[ft.Control] = [page_header(title, subtitle=subtitle, icon=icon, hue=hue, actions=actions)]
    if toolbar is not None:
        head.append(toolbar)
    return ft.Column(
        [ft.Column(head, spacing=SPACE_L, tight=True), ft.Container(expand=True, content=body)],
        expand=True,
        spacing=SPACE_XL,
    )


def card(
    title: str,
    children: list[ft.Control],
    *,
    description: str = "",
    action: ft.Control | None = None,
    icon: str = "",
    hue: str = "accent",
    divided: bool = False,
) -> ft.Container:
    """A surface with a heading (title, description and an action on the right), then its children.

    With `divided`, a hairline sits between the children. Rows made by `row_item` suit that.
    """
    colors = palette()
    heading: list[ft.Control] = []
    if icon:
        heading.append(icon_tile(icon, hue, size=ICON_ROW))
    heading_text: list[ft.Control] = [text(title, size=TYPE_TITLE, strong=True)]
    if description:
        heading_text.append(text(description, color=colors.muted))
    heading.append(ft.Column(heading_text, spacing=SPACE_XS, tight=True, expand=True))
    if action is not None:
        heading.append(action)

    body: list[ft.Control] = []
    for index, child in enumerate(children):
        if divided and index:
            body.append(hairline())
        body.append(child)

    content: list[ft.Control] = [ft.Row(heading, spacing=SPACE_M, vertical_alignment=ft.CrossAxisAlignment.CENTER)]
    if body:
        content.append(ft.Column(body, spacing=0, tight=True))
    return ft.Container(
        padding=CARD_PADDING,
        border_radius=RADIUS_CARD,
        bgcolor=colors.panel,
        border=ft.Border.all(1, colors.line),
        content=ft.Column(content, spacing=SPACE_L, tight=True),
    )


def row_item(
    title: str,
    description: str,
    action: ft.Control | None = None,
    *,
    icon: str | None = None,
    hue: str = "accent",
    on_click: Callable | None = None,
) -> ft.Container:
    """One row inside a card: an icon tile, the title and description, and the action on the right.

    A row with `on_click` is pressable as a whole, such as a link.
    """
    leading: list[ft.Control] = [icon_tile(icon, hue, size=ICON_ROW)] if icon else []
    trailing: list[ft.Control] = [action] if action is not None else []
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        border_radius=RADIUS_CONTROL,
        ink=on_click is not None,
        ink_color=ripple(),
        on_click=on_click,
        content=ft.Row(
            [
                *leading,
                ft.Column(
                    [
                        text(title, size=TYPE_LABEL, strong=True),
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


class StatusLine:
    """A coloured lamp and a label. Its colours are set with `set`, which also sends them to the page."""

    def __init__(self, label: str = "", color: str | None = None) -> None:
        self._dot = status_dot(color or palette().muted, size=10)
        self._label = text(label, size=TYPE_LABEL, strong=True)
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


class PillGroup:
    """Pills in a row where one is selected. The selected pill takes the accent tint.

    `options` is (value, label) pairs. `on_pick` gets the value of the pill that was pressed.
    """

    def __init__(self, options: tuple[tuple[str, str], ...], selected: str, on_pick: Callable[[str], None],
                 *, scroll: bool = False) -> None:
        self._on_pick = on_pick
        self._pills: dict[str, ft.Container] = {}
        for value, label in options:
            self._pills[value] = ft.Container(
                height=32,
                padding=ft.Padding.symmetric(horizontal=SPACE_L),
                border_radius=RADIUS_PILL,
                alignment=ft.Alignment.CENTER,
                ink=True,
                ink_color=ripple(),
                on_click=lambda _, key=value: self._on_pick(key),
                content=text(label, size=TYPE_BODY),
            )
        # A row, not a wrapping one: a wrapping row stretches each pill to the full width. Long lists scroll sideways.
        self.control = ft.Row(
            list(self._pills.values()),
            spacing=SPACE_S,
            scroll=ft.ScrollMode.AUTO if scroll else None,
        )
        self._paint(selected)

    def select(self, selected: str) -> None:
        self._paint(selected)
        for pill in self._pills.values():
            pill.update()
            pill.content.update()

    def _paint(self, selected: str) -> None:
        colors = palette()
        for value, pill in self._pills.items():
            chosen = value == selected
            pill.bgcolor = colors.accent_soft if chosen else None
            pill.border = ft.Border.all(1, colors.accent if chosen else colors.line)
            pill.content.color = colors.on_accent_soft if chosen else colors.muted
            pill.content.weight = ft.FontWeight.W_600 if chosen else None


class ProgressLine:
    """A bar and a line of text for a long job.

    The worker thread calls `feed` with each output line. The UI thread calls `tick` about every
    100 ms, through Window.run_job, so only the UI thread touches the controls.
    """

    def __init__(self) -> None:
        colors = palette()
        self._bar = ft.ProgressBar(value=None, color=colors.accent, bgcolor=colors.panel_high, bar_height=6,
                                   border_radius=RADIUS_TILE)
        self._text = text("", size=TYPE_CAPTION, color=colors.muted, mono=True, **ONE_LINE)
        self.control = ft.Column([self._bar, self._text], spacing=SPACE_S, tight=True, visible=False)
        self._percent: int | None = None
        self._line = ""

    def start(self, label: str) -> None:
        """Show the bar for a job that is starting. Call it on the UI thread."""
        self._percent = None
        self._line = label
        self.control.visible = True
        self._bar.value = None

    def feed(self, line: str) -> None:
        """Take one line of output. Safe to call from a worker thread."""
        self._line = line
        percent = percent_of(line)
        if percent is not None:
            self._percent = percent

    def tick(self) -> None:
        self._bar.value = None if self._percent is None else self._percent / 100
        self._text.value = self._line

    def hide(self) -> None:
        self.control.visible = False


def empty_state(
    title: str,
    body: str,
    *,
    icon: str = "",
    hue: str = "blue",
    spinner: bool = False,
    action: ft.Control | None = None,
) -> ft.Column:
    marker = ft.ProgressRing(width=28, height=28, stroke_width=2.5) if spinner else icon_tile(icon, hue, size=56)
    children: list[ft.Control] = [marker, text(title, size=TYPE_TITLE, strong=True)]
    if body:
        children.append(ft.Container(width=MEASURE_WIDTH, content=text(body, color=palette().muted, text_align=ft.TextAlign.CENTER)))
    if action is not None:
        children.append(action)
    return ft.Column(children, spacing=SPACE_M, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def device_state(device: Device | None) -> tuple[str, str]:
    """Human label and status colour for the device the user has selected."""
    colors = palette()
    if device is None:
        return t("No device selected"), colors.muted
    if device.is_ready:
        transport = _transport_label(device)
        return (t("Ready · {transport}", transport=transport) if transport else t("Ready")), colors.accent
    if device.mode == FASTBOOT:
        return t("Fastboot mode"), colors.signal
    labels = {
        "unauthorized": "Unauthorized",
        "offline": "Offline",
        "no permissions": "No permissions",
        "recovery": "Recovery",
        "sideload": "Sideload",
    }
    label = t(labels.get(device.state, device.state.capitalize()))
    if device.state in ("offline", "no permissions"):
        return label, colors.danger
    return label, colors.signal


def _transport_label(device: Device) -> str:
    return {"usb": "USB", "network": "Wi-Fi"}.get(device.transport, "")
