"""Screens take their sizes, spacing and buttons from the shared modules, so the look stays in one place."""

import ast
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "adb_toolkit" / "ui"
# theme.py defines the tokens and widgets.py builds the shared controls, so only they may hold literals.
EXEMPT = {UI / "theme.py", UI / "widgets.py"}
SPACING_SCALE = {0, 4, 8, 12, 16, 24, 32}
RAW_BUTTONS = {"FilledButton", "OutlinedButton", "TextButton", "FilledTonalButton", "ElevatedButton"}
TEXT_WIDGETS = {"text", "Text", "Icon"}


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return ""


def _violations() -> list[str]:
    found = []
    for path in sorted(UI.rglob("*.py")):
        if path in EXEMPT:
            continue
        where = path.relative_to(UI.parent.parent)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name in RAW_BUTTONS:
                found.append(f"{where}:{node.lineno} builds a raw {name}; use widgets.button()")
            for keyword in node.keywords:
                value = keyword.value
                if not (isinstance(value, ast.Constant) and isinstance(value.value, (int, float))):
                    continue
                if keyword.arg == "size" and name in TEXT_WIDGETS:
                    found.append(f"{where}:{node.lineno} sets a literal size={value.value}; use a TYPE_ constant")
                if keyword.arg == "spacing" and value.value not in SPACING_SCALE:
                    found.append(f"{where}:{node.lineno} spacing={value.value} is off the spacing scale")
    return found


def test_screens_use_the_shared_sizes_spacing_and_buttons():
    assert _violations() == []
