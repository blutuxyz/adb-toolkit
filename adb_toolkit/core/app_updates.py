"""Find the latest ADB Toolkit release on GitHub."""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from adb_toolkit.config import APP_RELEASES_API_URL, APP_RELEASES_PAGE_URL, APP_VERSION
from adb_toolkit.core.updates import UpdateError
from adb_toolkit.core.versions import Version


@dataclass(frozen=True)
class AppRelease:
    version: Version
    page_url: str


def parse_release(body: str) -> AppRelease:
    """Read the version tag and the release page from GitHub's latest-release JSON."""
    try:
        data = json.loads(body)
    except ValueError as error:
        raise UpdateError(f"GitHub sent a release that is not valid JSON: {error}") from error
    tag = data.get("tag_name") if isinstance(data, dict) else None
    try:
        version = Version.parse(str(tag or "").removeprefix("v"))
    except ValueError as error:
        raise UpdateError(f"The latest release has no readable version number: {tag!r}") from error
    return AppRelease(version=version, page_url=data.get("html_url") or APP_RELEASES_PAGE_URL)


def fetch_latest_release(timeout: float = 20) -> AppRelease | None:
    """Ask GitHub for the newest release. Returns None when the project has not published one yet."""
    request = urllib.request.Request(
        APP_RELEASES_API_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"ADB-Toolkit/{APP_VERSION}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise UpdateError(f"GitHub answered {error.code} when asked for the latest release.") from error
    except OSError as error:
        raise UpdateError(f"Could not reach GitHub: {error}") from error
    return parse_release(body)
