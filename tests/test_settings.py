from adb_toolkit.core import settings
from adb_toolkit.core.settings import AppSettings


def test_missing_file_gives_defaults(tmp_path):
    assert settings.load(tmp_path / "settings.json") == AppSettings(theme_mode="dark")


def test_round_trip_keeps_the_chosen_theme(tmp_path):
    path = tmp_path / "nested" / "settings.json"

    settings.save(path, AppSettings(theme_mode="light"))

    assert settings.load(path) == AppSettings(theme_mode="light")


def test_broken_json_gives_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")

    assert settings.load(path) == AppSettings()


def test_unknown_theme_value_is_replaced_with_the_default(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"theme_mode": "neon"}', encoding="utf-8")

    assert settings.load(path) == AppSettings(theme_mode="dark")
