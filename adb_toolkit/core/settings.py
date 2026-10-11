"""Settings kept between runs, stored as JSON in the user's data folder."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

LIGHT = "light"
DARK = "dark"
THEME_MODES = (LIGHT, DARK)


@dataclass
class AppSettings:
    theme_mode: str = DARK


def load(path: Path) -> AppSettings:
    """Read settings. Missing or broken files fall back to the defaults."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return AppSettings()
    if not isinstance(raw, dict):
        return AppSettings()
    theme = raw.get("theme_mode")
    return AppSettings(theme_mode=theme if theme in THEME_MODES else DARK)


def save(path: Path, settings: AppSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
