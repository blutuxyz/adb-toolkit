"""Put the platform-tools folder on PATH: for this process and, on Windows, for future sessions."""

import ctypes
import os
import sys
from pathlib import Path

_HWND_BROADCAST = 0xFFFF
_WM_SETTINGCHANGE = 0x001A
_SMTO_ABORTIFHUNG = 0x0002


def merge_path_entries(current: str, directory: str, separator: str = os.pathsep) -> str | None:
    """Append `directory` to a PATH value. Returns None if it is already listed."""
    entries = [entry for entry in current.split(separator) if entry.strip()]
    wanted = _normalize(directory)
    if any(_normalize(entry) == wanted for entry in entries):
        return None
    entries.append(directory)
    return separator.join(entries)


def ensure_on_path(directory: Path) -> bool:
    """Make `directory` reachable from PATH. Returns True if the user PATH changed."""
    text = str(directory)
    merged = merge_path_entries(os.environ.get("PATH", ""), text)
    if merged is not None:
        os.environ["PATH"] = merged
    if sys.platform == "win32":
        return _ensure_user_path_windows(text)
    return False


def _normalize(path: str) -> str:
    return os.path.normcase(os.path.normpath(path.strip().strip('"')))


def _ensure_user_path_windows(directory: str) -> bool:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, kind = "", winreg.REG_EXPAND_SZ
        merged = merge_path_entries(current, directory, separator=";")
        if merged is None:
            return False
        winreg.SetValueEx(key, "Path", 0, kind, merged)

    # Tell running programs (Explorer, terminals) that the environment changed.
    result = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(
        _HWND_BROADCAST, _WM_SETTINGCHANGE, 0, "Environment", _SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
    )
    return True
