"""Colour palettes, fonts and the Material 3 theme built from them.

The base is warm stone: the window reads as paper in light mode and as a warm
graphite in dark mode. Clay is the one action colour. Five identity hues (blue,
green, violet, amber, rose) each belong to one area of the app and show only in
its icons and their tinted tiles. Amber also marks things that need attention,
and red is reserved for destructive actions and failures.
"""

from dataclasses import dataclass

import flet as ft

from adb_toolkit.core.settings import DARK, LIGHT

FONT_REGULAR = "IBM Plex Sans"
FONT_MEDIUM = "IBM Plex Sans Medium"
FONT_SEMIBOLD = "IBM Plex Sans SemiBold"
FONT_MONO = "IBM Plex Mono"

# Paths are relative to the assets folder. Flet serves them to the window.
FONT_FILES = {
    FONT_REGULAR: "fonts/IBMPlexSans-Regular.ttf",
    FONT_MEDIUM: "fonts/IBMPlexSans-Medium.ttf",
    FONT_SEMIBOLD: "fonts/IBMPlexSans-SemiBold.ttf",
    FONT_MONO: "fonts/IBMPlexMono-Regular.ttf",
}

# Type scale. Screens use these names instead of literal font sizes.
TYPE_DISPLAY = 28  # screen titles and the brand name
TYPE_TITLE = 18  # section headers, dialog and empty-state titles
TYPE_LABEL = 15  # row titles and status lines (semibold)
TYPE_BODY = 14  # controls, body text and descriptions
TYPE_CAPTION = 12  # paths, counts, versions and other secondary detail

# Spacing scale. Every gap and padding is one of these.
SPACE_XS = 4
SPACE_S = 8
SPACE_M = 12
SPACE_L = 16
SPACE_XL = 24
SPACE_XXL = 32

# Shape. Controls are pills: buttons, filters, fields, navigation items and the device chip.
# Their radius is half their height. Surfaces (cards, dialogs, menus, snack bars) are
# rounded blocks with RADIUS_CARD. Icon tiles use RADIUS_TILE.
CONTROL_HEIGHT = 40  # buttons, filters, fields and navigation items
HEADER_CONTROL_HEIGHT = 48  # the top bar: device chip, Wi-Fi button and refresh
RADIUS_INSET = 6  # pieces inside a preview
RADIUS_TILE = 10  # icon tiles: the brand mark, letter tiles, the settings preview
RADIUS_CARD = 14  # surfaces: cards, dialogs, menus and snack bars

# Icons. Navigation and inline icons are outlined; tiles hold one at half their size.
ICON_NAV = 20
ICON_INLINE = 18
ICON_TILE = 40  # the default icon tile, and the indent that lines rows up under it

# Layout
SIDEBAR_WIDTH = 76  # the icon rail
TOPBAR_HEIGHT = 80  # the device strip
SPEC_LABEL_WIDTH = 220  # the left column of a spec section: its title and description
GUTTER = SPACE_XXL  # window edge to content, and the top bar's side padding
SECTION_GAP = SPACE_XXL  # between a screen's title, its sections, and between sections
ROW_PADDING = SPACE_L  # vertical padding of a list row
MEASURE_WIDTH = 440  # the widest text block: dialogs, empty states and the setup screen
SCROLL_PADDING = ft.Padding.only(right=SPACE_S)  # keeps a scrollbar off the content it scrolls

# Motion. Screens cross-fade and selections ease into place. Keep both short.
MOTION_SCREEN_MS = 220
MOTION_STATE_MS = 160


@dataclass(frozen=True)
class Palette:
    background: str  # window and sidebar
    bar: str  # top bar
    panel: str  # raised surfaces: device chip, theme choices
    panel_high: str  # hover and inset surfaces
    line: str  # hairlines and dividers only
    control_border: str  # outlines of fields, segmented buttons and outlined buttons, at 3:1
    text: str
    muted: str
    accent: str  # clay: the one brand colour and action colour
    on_accent: str
    accent_soft: str  # selected navigation item
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
    background="#F5F2EE",
    bar="#FFFFFF",
    panel="#FFFFFF",
    panel_high="#EAE5DE",
    line="#D9D2C8",
    control_border="#7F776B",
    text="#1F1B17",
    muted="#5E5649",
    accent="#A3432A",
    on_accent="#FFFFFF",
    accent_soft="#F6DDD4",
    on_accent_soft="#5C1F10",
    signal="#8A5A00",
    on_signal="#FFFFFF",
    danger="#C62828",
    on_danger="#FFFFFF",
    blue="#2563EB",
    green="#15803D",
    violet="#6D3FD6",
    amber="#8A5A00",
    rose="#C2185B",
)

DARK_PALETTE = Palette(
    background="#171411",
    bar="#1F1A16",
    panel="#27211C",
    panel_high="#342E27",
    line="#463E35",
    control_border="#7D7467",
    text="#F6F1EB",
    muted="#B9AEA0",
    accent="#F2A58A",
    on_accent="#3A1508",
    accent_soft="#4A2A20",
    on_accent_soft="#FFDCCF",
    signal="#FFC46B",
    on_signal="#171411",
    danger="#FF7D7D",
    on_danger="#171411",
    blue="#7DB4FF",
    green="#6FE3A0",
    violet="#B9A4FF",
    amber="#FFC46B",
    rose="#FF97B4",
)

PALETTES = {LIGHT: LIGHT_PALETTE, DARK: DARK_PALETTE}

_active = DARK_PALETTE


def activate(palette: Palette) -> None:
    """Choose the palette the next widgets are built with."""
    global _active
    _active = palette


def palette() -> Palette:
    return _active


def build_theme(colors: Palette) -> ft.Theme:
    return ft.Theme(
        font_family=FONT_REGULAR,
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
