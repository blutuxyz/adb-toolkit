"""Text size and language are saved with the theme, and a broken value falls back one setting at a time."""

import json

import pytest

from adb_toolkit.core.session import Session
from adb_toolkit.core.settings import DARK, FONT_SCALES, AppSettings, load, save


def test_the_defaults_apply_when_no_file_exists(tmp_path):
    assert load(tmp_path / "settings.json") == AppSettings(theme_mode=DARK, font_scale="default", language="en")


def test_the_new_settings_survive_a_save_and_load(tmp_path):
    path = tmp_path / "settings.json"
    chosen = AppSettings(theme_mode="light", font_scale="large", language="de")

    save(path, chosen)

    assert load(path) == chosen


def test_an_unknown_value_falls_back_only_for_that_setting(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme_mode": "light", "font_scale": "huge", "language": "fr"}), encoding="utf-8")

    assert load(path) == AppSettings(theme_mode="light", font_scale="default", language="en")


def test_a_file_that_is_not_an_object_gives_the_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1, 2]", encoding="utf-8")

    assert load(path) == AppSettings()


def test_the_text_sizes_are_small_default_and_large():
    assert set(FONT_SCALES) == {"small", "default", "large"}
    assert FONT_SCALES["default"] == 1.0


def test_the_session_saves_changes_and_refuses_unknown_settings(tmp_path):
    path = tmp_path / "settings.json"
    session = Session(settings_path=path)

    session.set_settings(font_scale="large", language="de")

    assert load(path).font_scale == "large"
    assert load(path).language == "de"
    with pytest.raises(ValueError):
        session.set_settings(volume="loud")
