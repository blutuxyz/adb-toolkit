"""The palettes must stay readable in both themes, and the letter tiles must keep their colours."""

import pytest

from adb_toolkit.ui.theme import DARK_PALETTE, LIGHT_PALETTE
from adb_toolkit.ui.widgets import letter_hue

THEMES = [("light", LIGHT_PALETTE), ("dark", DARK_PALETTE)]
IDENTITY_HUES = ("blue", "green", "violet", "amber", "rose")


def _luminance(hex_colour: str) -> float:
    """Relative luminance from WCAG 2.x."""
    value = hex_colour.lstrip("#")
    linear = []
    for start in (0, 2, 4):
        channel = int(value[start:start + 2], 16) / 255
        linear.append(channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4)
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(first: str, second: str) -> float:
    brighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (brighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("theme, colours", THEMES)
@pytest.mark.parametrize("foreground, background", [
    ("text", "background"),
    ("text", "panel"),
    ("text", "bar"),
    ("muted", "background"),
    ("muted", "panel"),
])
def test_text_meets_aa_on_every_surface(theme, colours, foreground, background):
    ratio = _contrast(getattr(colours, foreground), getattr(colours, background))

    assert ratio >= 4.5, f"{theme}: {foreground} on {background} is {ratio:.2f}:1"


@pytest.mark.parametrize("theme, colours", THEMES)
def test_label_on_the_accent_button_meets_aa(theme, colours):
    ratio = _contrast(colours.on_accent, colours.accent)

    assert ratio >= 4.5, f"{theme}: button label is {ratio:.2f}:1"


@pytest.mark.parametrize("theme, colours", THEMES)
@pytest.mark.parametrize("hue", IDENTITY_HUES + ("accent", "danger"))
def test_icons_stand_out_on_the_panels(theme, colours, hue):
    ratio = _contrast(getattr(colours, hue), colours.panel)

    assert ratio >= 3, f"{theme}: {hue} icon on the panel is {ratio:.2f}:1"


def test_a_package_keeps_its_letter_colour_between_runs():
    assert letter_hue("com.android.chrome") == letter_hue("com.android.chrome")


def test_letter_tiles_only_use_palette_hues():
    packages = ["com.android.chrome", "com.spotify.music", "org.telegram.messenger", "com.example.notes"]

    hues = {letter_hue(package) for package in packages}

    assert hues <= set(IDENTITY_HUES) | {"accent"}
