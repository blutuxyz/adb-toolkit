import urllib.error
import urllib.request

import pytest

from adb_toolkit.config import APP_RELEASES_PAGE_URL, APP_VERSION
from adb_toolkit.core import app_updates
from adb_toolkit.core.adb import Adb
from adb_toolkit.core.app_updates import AppRelease, fetch_latest_release, parse_release
from adb_toolkit.core.fastboot import Fastboot
from adb_toolkit.core.session import Session
from adb_toolkit.core.updates import UpdateError
from adb_toolkit.core.versions import Version

RELEASE = (
    '{"tag_name": "v0.2.0",'
    ' "html_url": "https://github.com/blutuxyz/adb-toolkit/releases/tag/v0.2.0"}'
)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def read(self) -> bytes:
        return self._body


def _answer(monkeypatch, result) -> list:
    """Replace urlopen. `result` is returned, or raised if it is an exception. Returns the requests seen."""
    seen = []

    def fake_urlopen(request, timeout):
        seen.append(request)
        if isinstance(result, BaseException):
            raise result
        return _Response(result)

    monkeypatch.setattr(app_updates.urllib.request, "urlopen", fake_urlopen)
    return seen


def test_reads_the_version_and_page_from_the_release():
    release = parse_release(RELEASE)

    assert release.version == Version(0, 2, 0)
    assert release.page_url == "https://github.com/blutuxyz/adb-toolkit/releases/tag/v0.2.0"


def test_a_tag_without_the_v_prefix_is_read_too():
    assert parse_release('{"tag_name": "1.0.0"}').version == Version(1, 0, 0)


def test_a_missing_page_link_falls_back_to_the_releases_page():
    assert parse_release('{"tag_name": "v0.2.0"}').page_url == APP_RELEASES_PAGE_URL


def test_a_tag_that_is_not_a_version_is_an_error():
    with pytest.raises(UpdateError):
        parse_release('{"tag_name": "nightly"}')


def test_a_body_that_is_not_json_is_an_error():
    with pytest.raises(UpdateError):
        parse_release("<html>Not Found</html>")


def test_fetch_returns_the_latest_release(monkeypatch):
    _answer(monkeypatch, RELEASE.encode("utf-8"))

    assert fetch_latest_release().version == Version(0, 2, 0)


def test_fetch_identifies_the_app_to_github(monkeypatch):
    seen = _answer(monkeypatch, RELEASE.encode("utf-8"))

    fetch_latest_release()

    request = seen[0]
    assert request.get_header("User-agent") == f"ADB-Toolkit/{APP_VERSION}"
    assert request.get_header("Accept") == "application/vnd.github+json"


def test_no_release_yet_is_none_not_an_error(monkeypatch):
    not_found = urllib.error.HTTPError("https://api.github.test", 404, "Not Found", hdrs=None, fp=None)
    _answer(monkeypatch, not_found)

    assert fetch_latest_release() is None


def test_other_http_errors_are_reported(monkeypatch):
    server_error = urllib.error.HTTPError("https://api.github.test", 500, "Server Error", hdrs=None, fp=None)
    _answer(monkeypatch, server_error)

    with pytest.raises(UpdateError, match="500"):
        fetch_latest_release()


def test_being_offline_is_reported(monkeypatch):
    _answer(monkeypatch, urllib.error.URLError("no route to host"))

    with pytest.raises(UpdateError, match="Could not reach GitHub"):
        fetch_latest_release()


def _session(tmp_path) -> Session:
    return Session(
        adb=Adb(executable="adb-not-used"),
        fastboot=Fastboot(executable="fastboot-not-used"),
        settings_path=tmp_path / "settings.json",
    )


def test_no_app_release_means_no_app_update(tmp_path):
    session = _session(tmp_path)

    assert session.app_update_available is False


def test_the_same_app_version_is_not_an_update(tmp_path):
    session = _session(tmp_path)
    session.app_release = AppRelease(Version.parse(APP_VERSION), "https://example.test/release")

    assert session.app_update_available is False


def test_a_newer_app_release_is_an_update(tmp_path):
    session = _session(tmp_path)
    session.app_release = AppRelease(Version(99, 0, 0), "https://example.test/release")

    assert session.app_update_available is True
