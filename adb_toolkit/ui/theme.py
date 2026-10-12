"""Colour palettes, fonts and the Material 3 theme built from them.

The base is a cool slate, lifted enough that the window reads as bright rather
than murky. Teal is the one action colour. Five identity hues (blue, green,
violet, amber, rose) each belong to one area of the app and show only in its
icons and their tinted tiles. Amber also marks things that need attention, and
red is reserved for destructive actions and failures.
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

# Shape and spacing. Screens use these names instead of literal numbers.
# Controls are pills: buttons, filters, fields, navigation items and the device chip.
# Their radius is half their height. Surfaces (cards, dialogs, menus, snack bars) are
# rounded blocks with RADIUS_CARD. Icon tiles use RADIUS_TILE.
CONTROL_HEIGHT = 40  # buttons, filters, fields and navigation items
HEADER_CONTROL_HEIGHT = 48  # the top bar: device chip, Wi-Fi button and refresh
RADIUS_INSET = 6  # pieces inside a preview
RADIUS_TILE = 10  # icon tiles: the brand mark, letter tiles, the settings preview
RADIUS_CARD = 14  # surfaces: cards, dialogs, menus and snack bars
GUTTER = 36  # window edge to content, and the top bar's side padding
SECTION_GAP = 32  # between a screen's title block and its content
ROW_PADDING = 16  # vertical padding of a list row
SCROLL_PADDING = ft.Padding.only(right=8)  # keeps a scrollbar off the content it scrolls

# Motion. Screens cross-fade and selections ease into place. Keep both short.
MOTION_SCREEN_MS = 220
MOTION_STATE_MS = 160


@dataclass(frozen=True)
class Palette:
    background: str  # window and sidebar
    bar: str  # top bar
    panel: str  # raised surfaces: device chip, theme choices
    panel_high: str  # hover and inset surfaces
    line: str  # hairlines and outlines
    text: str
    muted: str
    accent: str  # Oxide: the one brand colour
    on_accent: str
    accent_soft: str  # selected navigation item
    on_accent_soft: str
    signal: str  # needs attention: updates, unauthorised devices
    danger: str  # destructive actions and failed devices
    # Identity hues. Each area of the app owns one; they tint icon tiles and never fill large areas.
    blue: str
    green: str
    violet: str
    amber: str
    rose: str


LIGHT_PALETTE = Palette(
    background="#F2F5F9",
    bar="#FFFFFF",
    panel="#FFFFFF",
    panel_high="#E6ECF3",
    line="#D3DCE7",
    text="#142033",
    muted="#56657A",
    accent="#0B7D72",
    on_accent="#FFFFFF",
    accent_soft="#CFF2EB",
    on_accent_soft="#03423D",
    signal="#A85D00",
    danger="#C62828",
    blue="#2563EB",
    green="#15803D",
    violet="#6D3FD6",
    amber="#A85D00",
    rose="#C2185B",
)

DARK_PALETTE = Palette(
    background="#151B26",
    bar="#1B2331",
    panel="#232D3D",
    panel_high="#2E3A4E",
    line="#39475C",
    text="#F1F5FA",
    muted="#A9B6C9",
    accent="#4FD8C6",
    on_accent="#03262A",
    accent_soft="#1B4A4F",
    on_accent_soft="#C8F7EE",
    signal="#FFC46B",
    danger="#FF7D7D",
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
