"""App-wide constants: names, links and where platform-tools come from."""

from pathlib import Path

APP_NAME = "ADB Toolkit"
APP_VERSION = "0.1.0"

CREATOR_NAME = "blutu"
CREATOR_URL = "https://blutu.xyz"
PROJECT_URL = "https://github.com/blutuxyz/adb-toolkit"

# Google publishes the SDK package list here. It names the latest platform-tools
# revision and gives a download URL and SHA-1 for each operating system.
PLATFORM_TOOLS_REPOSITORY_URL = "https://dl.google.com/android/repository/repository2-3.xml"
PLATFORM_TOOLS_BASE_URL = "https://dl.google.com/android/repository/"

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
