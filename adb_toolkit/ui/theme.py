"""Colour palettes, type and the Material theme built from them.

The base is a cool graphite: the window is a near-black slate in dark mode and a pale
blue-grey in light mode. Teal is the one action colour. Five identity hues (blue, green,
violet, amber, rose) each belong to one area of the app and show only in its icons and
the tint of their tiles. Amber also marks things that need attention, and red is reserved
for destructive actions and failures.
"""

from dataclasses import dataclass

import flet as ft

from adb_toolkit.core.settings import DARK, LIGHT

# Segoe UI ships with Windows, so the sans face is read from the system. The mono face is
# bundled, so serials, versions and paths look the same on every machine.
FONT_SANS = "Segoe UI"
FONT_MONO = "IBM Plex Mono"

# Paths are relative to the assets folder. Flet serves them to the window.
FONT_FILES = {
    FONT_MONO: "fonts/IBMPlexMono-Regular.ttf",
}

# Type scale. Screens use these names instead of literal font sizes. Weight is set with
# `strong` on text(), not with a separate font family.
TYPE_DISPLAY = 26  # screen titles and the brand name
TYPE_TITLE = 17  # card titles, dialog and empty-state titles
TYPE_LABEL = 15  # row titles and status lines (strong)
TYPE_BODY = 14  # controls, body text and descriptions
TYPE_CAPTION = 12  # paths, counts, versions, group labels and other secondary detail

# Spacing scale. Every gap and padding is one of these.
SPACE_XS = 4
SPACE_S = 8
SPACE_M = 12
SPACE_L = 16
SPACE_XL = 24
SPACE_XXL = 32

# Shape. Controls are squared-off rounded rectangles (buttons, fields, navigation items).
# Chips and the status pills are fully round. Surfaces (cards, dialogs, menus, snack bars) use
# RADIUS_CARD. Icon tiles and the brand mark use RADIUS_TILE.
CONTROL_HEIGHT = 40  # buttons, fields and navigation items
RADIUS_CONTROL = 10
RADIUS_PILL = 999  # chips, tags and the device lamp
RADIUS_INSET = 6  # pieces inside a preview
RADIUS_TILE = 10  # icon tiles and the brand mark
RADIUS_CARD = 16  # surfaces: cards, dialogs, menus and snack bars

# Icons. Navigation and inline icons are outlined; tiles hold one at half their size.
ICON_NAV = 18
ICON_INLINE = 16
ICON_ROW = 36  # the icon tile at the start of a row or card header
ICON_TILE = 44  # the icon tile of a screen header and a dialog

# Layout
SIDEBAR_WIDTH = 264  # the navigation column, with the device picker at its top
GUTTER = SPACE_XXL  # window edge to content on every side
SECTION_GAP = SPACE_L  # between the cards of one screen
CARD_PADDING = SPACE_XL  # inside a card
ROW_PADDING = SPACE_M  # vertical padding of a row inside a card
MEASURE_WIDTH = 440  # the widest text block: dialogs, empty states and the setup panel
SCROLL_PADDING = ft.Padding.only(right=SPACE_S)  # keeps a scrollbar off the content it scrolls

# Motion. Screens cross-fade and selections ease into place. Keep both short.
MOTION_SCREEN_MS = 220
MOTION_STATE_MS = 160


@dataclass(frozen=True)
class Palette:
    background: str  # window
    bar: str  # navigation column
    panel: str  # cards, the device picker, menus
    panel_high: str  # hover and inset surfaces
    line: str  # hairlines and dividers only
    control_border: str  # outlines of fields and outlined buttons, at 3:1
    text: str
    muted: str
    accent: str  # teal: the one brand colour and action colour
    on_accent: str
    accent_soft: str  # selected navigation item and selected chip
    on_accent_soft: str
    signal: str  # needs attention: updates, unauthorised devices
    on_signal: str  # text on a signal fill, such as the update tag
    danger: str  # destructive actions and failed devices
    on_danger: str  # text on a danger fill
    # Identity hues. Each area of the app owns one; they tint icon tiles and never fill large areas.
    blue: str
    green: str
    violet: str
    amber: str
    rose: str


LIGHT_PALETTE = Palette(
    background="#F3F5F9",
    bar="#FFFFFF",
    panel="#FFFFFF",
    panel_high="#E9EDF4",
    line="#D7DEE9",
    control_border="#6B7689",
    text="#0E1520",
    muted="#4B5669",
    accent="#0A7268",
    on_accent="#FFFFFF",
    accent_soft="#D2EFE9",
    on_accent_soft="#053A34",
    signal="#8A5A00",
    on_signal="#FFFFFF",
    danger="#C62828",
    on_danger="#FFFFFF",
    blue="#1D4ED8",
    green="#15803D",
    violet="#6D28D9",
    amber="#8A5A00",
    rose="#BE185D",
)

DARK_PALETTE = Palette(
    background="#0D1117",
    bar="#11161D",
    panel="#161C25",
    panel_high="#1F2733",
    line="#273141",
    control_border="#687385",
    text="#E6EDF3",
    muted="#8B98A9",
    accent="#2DD4BF",
    on_accent="#04201C",
    accent_soft="#143834",
    on_accent_soft="#99F6E4",
    signal="#FBBF24",
    on_signal="#1C1400",
    danger="#F87171",
    on_danger="#1C0505",
    blue="#60A5FA",
    green="#4ADE80",
    violet="#A78BFA",
    amber="#FBBF24",
    rose="#F472B6",
)

PALETTES = {LIGHT: LIGHT_PALETTE, DARK: DARK_PALETTE}

_active = DARK_PALETTE
_text_scale = 1.0


def activate(palette: Palette) -> None:
    """Choose the palette the next widgets are built with."""
    global _active
    _active = palette


def palette() -> Palette:
    return _active


def activate_text_scale(scale: float) -> None:
    """Choose the factor the text sizes are multiplied by. Set from the font size setting."""
    global _text_scale
    _text_scale = scale


def text_scale() -> float:
    return _text_scale


def build_theme(colors: Palette) -> ft.Theme:
    return ft.Theme(
        font_family=FONT_SANS,
        color_scheme=ft.ColorScheme(
            primary=colors.accent,
            on_primary=colors.on_accent,
            primary_container=colors.accent_soft,
            on_primary_container=colors.on_accent_soft,
            secondary=colors.muted,
            on_secondary=colors.background,
            secondary_container=colors.panel_high,
            on_secondary_container=colors.text,
            tertiary=colors.signal,
            on_tertiary=colors.background,
            error=colors.danger,
            on_error=colors.background,
            surface=colors.background,
            on_surface=colors.text,
            on_surface_variant=colors.muted,
            surface_container_lowest=colors.bar,
            surface_container_low=colors.background,
            surface_container=colors.panel,
            surface_container_high=colors.panel_high,
            surface_container_highest=colors.line,
            outline=colors.muted,
            outline_variant=colors.line,
        ),
    )
