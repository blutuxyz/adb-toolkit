"""Settings kept between runs, stored as JSON in the user's data folder."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

LIGHT = "light"
DARK = "dark"
THEME_MODES = (LIGHT, DARK)

# The text size is a name in the file and a factor for the screens.
FONT_SCALES = {"small": 0.9, "default": 1.0, "large": 1.15}
ENGLISH = "en"
GERMAN = "de"
LANGUAGES = (ENGLISH, GERMAN)


@dataclass
class AppSettings:
    theme_mode: str = DARK
    font_scale: str = "default"
    language: str = ENGLISH


def load(path: Path) -> AppSettings:
    """Read settings. Missing or broken files fall back to the defaults, one value at a time."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return AppSettings()
    if not isinstance(raw, dict):
        return AppSettings()
    defaults = AppSettings()
    return AppSettings(
        theme_mode=_allowed(raw.get("theme_mode"), THEME_MODES, defaults.theme_mode),
        font_scale=_allowed(raw.get("font_scale"), tuple(FONT_SCALES), defaults.font_scale),
        language=_allowed(raw.get("language"), LANGUAGES, defaults.language),
    )


def save(path: Path, settings: AppSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


def _allowed(value, choices: tuple[str, ...], default: str) -> str:
    return value if value in choices else default
