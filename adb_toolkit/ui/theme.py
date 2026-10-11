"""Colour palettes, fonts and the Material 3 theme built from them.

The palette is cool and slightly green: Sage Paper for the background, Ink for
text, and Oxide teal as the one accent. Amber marks things that need attention.
Other colours are for status only.
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


LIGHT_PALETTE = Palette(
    background="#EDF0EE",
    bar="#F7F9F8",
    panel="#FBFCFB",
    panel_high="#E1E7E4",
    line="#D2DAD6",
    text="#1A1F1E",
    muted="#5C6764",
    accent="#0E6B63",
    on_accent="#FFFFFF",
    accent_soft="#CFE8E3",
    on_accent_soft="#063B36",
    signal="#8F5511",
    danger="#B3261E",
)

DARK_PALETTE = Palette(
    background="#101716",
    bar="#152120",
    panel="#1A2725",
    panel_high="#24332F",
    line="#2B3B37",
    text="#E2EAE7",
    muted="#97A6A2",
    accent="#6FD0C2",
    on_accent="#00332E",
    accent_soft="#173F3A",
    on_accent_soft="#BFEFE6",
    signal="#E9B35F",
    danger="#F2B8B5",
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
