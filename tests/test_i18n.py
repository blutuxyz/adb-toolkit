"""Every string the UI shows through t() has a German entry, and German text is never shown in English mode."""

import ast
from pathlib import Path

import pytest

from adb_toolkit.ui import i18n
from adb_toolkit.ui.i18n import activate_language, t

UI = Path(__file__).resolve().parents[1] / "adb_toolkit" / "ui"

# Labels held in module-level tuples. They are translated when a screen is built, so no t() call names them.
_DEVICE_STATES = ("Unauthorized", "Offline", "No permissions", "Recovery", "Sideload")
_PACKAGE_TAGS = ("Removed system app", "System app", "User app")


def _literal_keys() -> set[str]:
    """Every string literal passed as the first argument of t() anywhere in the UI."""
    keys: set[str] = set()
    for path in UI.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "t" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    keys.add(first.value)
    return keys


def _module_label_keys() -> set[str]:
    from adb_toolkit.ui.sidebar import APP_ITEMS, TOOL_ITEMS
    from adb_toolkit.ui.views.adb_tools import _TARGETS as ADB_TARGETS
    from adb_toolkit.ui.views.apps import FILTERS
    from adb_toolkit.ui.views.capture import _DURATIONS
    from adb_toolkit.ui.views.fastboot_tools import _TARGETS as FASTBOOT_TARGETS
    from adb_toolkit.ui.views.mirror import _SIZES
    from adb_toolkit.ui.views.settings import _SIZE_LABELS, _THEME_LABELS

    keys = {label for _key, label, _icon, _hue in (*TOOL_ITEMS, *APP_ITEMS)}
    for target in (*ADB_TARGETS, *FASTBOOT_TARGETS):
        keys.update({target.title, target.description, target.done})
    keys.update(label for _value, label in FILTERS)
    keys.update(label for _value, label in _DURATIONS)
    keys.update(label for _value, label in _SIZES)
    keys.update(label for _mode, label, _icon, _hue in _THEME_LABELS)
    keys.update(label for _value, label in _SIZE_LABELS)
    keys.update(_DEVICE_STATES)
    keys.update(_PACKAGE_TAGS)
    return keys


def test_every_shown_string_has_a_german_entry():
    needed = _literal_keys() | _module_label_keys()

    missing = sorted(key for key in needed if key not in i18n._GERMAN)

    assert missing == [], f"no German entry for: {missing}"


def test_no_german_entry_is_left_unused():
    needed = _literal_keys() | _module_label_keys()
    # Pill labels that are numbers or units are not translated, so they are not in the table.
    unused = sorted(set(i18n._GERMAN) - needed)

    assert unused == [], f"German entries nothing uses: {unused}"


@pytest.fixture(autouse=True)
def _english():
    activate_language("en")
    yield
    activate_language("en")


def test_english_is_the_default_and_shows_the_text_unchanged():
    assert t("Reboot") == "Reboot"


def test_german_is_shown_when_it_is_the_active_language():
    activate_language("de")

    assert t("Reboot") == "Neu starten"


def test_a_string_without_a_german_entry_falls_back_to_english():
    activate_language("de")

    assert t("A string nobody translated") == "A string nobody translated"


def test_values_fill_the_placeholders_in_either_language():
    assert t("Installed {name}", name="x.apk") == "Installed x.apk"
    activate_language("de")
    assert t("Installed {name}", name="x.apk") == "x.apk installiert"


def test_an_unknown_language_code_means_english():
    activate_language("fr")

    assert i18n.language() == "en"
