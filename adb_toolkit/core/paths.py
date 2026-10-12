"""Where the toolkit keeps its own files: downloaded tools and settings."""

import os
import sys
from pathlib import Path

from adb_toolkit.config import APP_NAME


def data_dir() -> Path:
    """Per-user folder for the toolkit's files. Created on first use."""
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def platform_tools_dir() -> Path:
    """Folder that holds our copy of adb and fastboot."""
    return data_dir() / "platform-tools"


def settings_file() -> Path:
    return data_dir() / "settings.json"


def scrcpy_dir() -> Path:
    """Folder the toolkit looks in for scrcpy, before it looks on PATH."""
    return data_dir() / "scrcpy"


def scrcpy_log() -> Path:
    return data_dir() / "scrcpy.log"
