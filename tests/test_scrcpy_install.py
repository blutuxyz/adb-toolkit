import hashlib
import io
import json
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

from adb_toolkit.core import scrcpy_install
from adb_toolkit.core.scrcpy import EXECUTABLE_NAME
from adb_toolkit.core.scrcpy_install import (
    RemoteScrcpy,
    ScrcpyInstallError,
    asset_prefix,
    checksum_from_sums,
    download,
    fetch_latest,
    install_archive,
    parse_release,
)
from adb_toolkit.core.versions import Version

WIN64_URL = "https://github.com/Genymobile/scrcpy/releases/download/v5.0.1/scrcpy-win64-v5.0.1.zip"
SUMS_URL = "https://github.com/Genymobile/scrcpy/releases/download/v5.0.1/SHA256SUMS.txt"


def _release(*, digest: str | None = "sha256:ABC123", tag: str = "v5.0.1") -> str:
    def asset(name: str, **extra) -> dict:
        url = f"https://github.com/Genymobile/scrcpy/releases/download/{tag}/{name}"
        return {"name": name, "size": 100, "browser_download_url": url, **extra}

    extra = {"digest": digest} if digest else {}
    return json.dumps(
        {
            "tag_name": tag,
            "assets": [
                asset("scrcpy-linux-x86_64-v5.0.1.tar.gz", **extra),
                asset("scrcpy-server-v5.0.1"),
                asset("scrcpy-win32-v5.0.1.zip", **extra),
                asset("scrcpy-win64-v5.0.1.zip", **extra),
                asset("SHA256SUMS.txt"),
            ],
        }
    )


def _zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


def _tar(path: Path, members: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755
            archive.addfile(info, io.BytesIO(data))
    return path


@pytest.mark.parametrize(
    ("platform", "machine", "prefix"),
    [
        ("win32", "AMD64", "scrcpy-win64-"),
        ("win32", "ARM64", "scrcpy-winarm64-"),
        ("win32", "x86", "scrcpy-win32-"),
        ("darwin", "arm64", "scrcpy-macos-aarch64-"),
        ("darwin", "x86_64", "scrcpy-macos-x86_64-"),
        ("linux", "x86_64", "scrcpy-linux-x86_64-"),
        ("linux", "armv7l", None),
        ("freebsd14", "amd64", None),
    ],
)
def test_each_system_gets_its_own_build(platform, machine, prefix):
    assert asset_prefix(platform, machine) == prefix


def test_the_release_names_the_build_version_and_checksum_for_this_system():
    remote, _ = parse_release(_release(), "win32", "AMD64")

    assert remote.version == Version(5, 0, 1)
    assert remote.url == WIN64_URL
    assert remote.file_name == "scrcpy-win64-v5.0.1.zip"
    assert remote.sha256 == "abc123"


def test_a_release_without_digests_points_at_the_checksum_file():
    remote, sums_url = parse_release(_release(digest=None), "win32", "AMD64")

    assert remote.sha256 == ""
    assert sums_url == SUMS_URL


def test_a_system_with_no_build_is_reported():
    with pytest.raises(ScrcpyInstallError, match="no build"):
        parse_release(_release(), "linux", "armv7l")


def test_a_release_without_this_systems_archive_is_reported():
    with pytest.raises(ScrcpyInstallError, match="no download"):
        parse_release(_release(), "darwin", "arm64")


def test_a_release_that_is_not_json_is_reported():
    with pytest.raises(ScrcpyInstallError, match="not valid JSON"):
        parse_release("<html>", "win32", "AMD64")


def test_a_tag_that_is_not_a_version_is_reported():
    with pytest.raises(ScrcpyInstallError, match="version number"):
        parse_release(_release(tag="nightly"), "win32", "AMD64")


def test_the_checksum_is_found_in_a_sha256sum_listing():
    listing = "AAA111  scrcpy-win64-v5.0.1.zip\nbbb222 *scrcpy-win32-v5.0.1.zip\n"

    assert checksum_from_sums(listing, "scrcpy-win64-v5.0.1.zip") == "aaa111"
    assert checksum_from_sums(listing, "scrcpy-win32-v5.0.1.zip") == "bbb222"
    assert checksum_from_sums(listing, "other.zip") == ""


def test_fetch_latest_reads_the_checksum_file_when_the_build_has_no_digest(monkeypatch):
    checksum = "f" * 64
    bodies = {
        scrcpy_install.SCRCPY_RELEASES_API_URL: _release(digest=None),
        SUMS_URL: f"{checksum}  scrcpy-win64-v5.0.1.zip\n",
    }
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda request, timeout=None: io.BytesIO(bodies[request.full_url].encode())
    )

    remote = fetch_latest(sys_platform="win32", machine="AMD64")

    assert remote.sha256 == checksum


def test_fetch_latest_reports_an_unreachable_github(monkeypatch):
    def offline(*args, **kwargs):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(urllib.request, "urlopen", offline)

    with pytest.raises(ScrcpyInstallError, match="Could not reach GitHub"):
        fetch_latest(sys_platform="win32", machine="AMD64")


def test_download_saves_the_file_when_the_checksum_matches(tmp_path, monkeypatch):
    payload = b"scrcpy bytes" * 1000
    remote = RemoteScrcpy(Version(5, 0, 1), WIN64_URL, len(payload), hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(payload))
    calls = []

    destination = tmp_path / "scrcpy.zip"
    download(remote, destination, progress=lambda done, total: calls.append((done, total)))

    assert destination.read_bytes() == payload
    assert calls[-1] == (len(payload), len(payload))


def test_download_with_the_wrong_checksum_is_deleted_and_reported(tmp_path, monkeypatch):
    remote = RemoteScrcpy(Version(5, 0, 1), WIN64_URL, 8, "0" * 64)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b"tampered"))
    destination = tmp_path / "scrcpy.zip"

    with pytest.raises(ScrcpyInstallError, match="checksum"):
        download(remote, destination)

    assert not destination.exists()


def test_download_without_a_known_checksum_is_refused_before_any_request(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("nothing should be requested")

    monkeypatch.setattr(urllib.request, "urlopen", fail)

    with pytest.raises(ScrcpyInstallError, match="no checksum"):
        download(RemoteScrcpy(Version(5, 0, 1), WIN64_URL, 8, ""), tmp_path / "scrcpy.zip")


def test_download_refuses_a_plain_http_address(tmp_path):
    remote = RemoteScrcpy(Version(5, 0, 1), "http://example.test/scrcpy.zip", 8, "0" * 64)

    with pytest.raises(ScrcpyInstallError, match="HTTPS"):
        download(remote, tmp_path / "scrcpy.zip")


def test_install_puts_the_programs_folder_at_the_target(tmp_path):
    archive = _zip(
        tmp_path / "scrcpy.zip",
        {
            f"scrcpy-win64-v5.0.1/{EXECUTABLE_NAME}": b"new",
            "scrcpy-win64-v5.0.1/scrcpy-server": b"server",
        },
    )
    target = tmp_path / "data" / "scrcpy"

    install_archive(archive, target)

    assert (target / EXECUTABLE_NAME).read_bytes() == b"new"
    assert (target / "scrcpy-server").read_bytes() == b"server"
    assert not (target.parent / "scrcpy.previous").exists()


def test_install_reads_a_tar_archive(tmp_path):
    archive = _tar(tmp_path / "scrcpy.tar.gz", {f"scrcpy-linux-x86_64-v5.0.1/{EXECUTABLE_NAME}": b"new"})

    install_archive(archive, tmp_path / "scrcpy")

    assert (tmp_path / "scrcpy" / EXECUTABLE_NAME).read_bytes() == b"new"


def test_reinstall_replaces_the_old_copy_completely(tmp_path):
    target = tmp_path / "scrcpy"
    target.mkdir()
    (target / "stale.dll").write_bytes(b"old")
    (target / EXECUTABLE_NAME).write_bytes(b"old")

    install_archive(_zip(tmp_path / "scrcpy.zip", {f"s/{EXECUTABLE_NAME}": b"new"}), target)

    assert not (target / "stale.dll").exists()
    assert (target / EXECUTABLE_NAME).read_bytes() == b"new"


def test_an_archive_without_the_program_leaves_the_old_copy_alone(tmp_path):
    target = tmp_path / "scrcpy"
    target.mkdir()
    (target / EXECUTABLE_NAME).write_bytes(b"old")

    with pytest.raises(ScrcpyInstallError, match="does not contain"):
        install_archive(_zip(tmp_path / "bad.zip", {"readme.txt": b"nothing"}), target)

    assert (target / EXECUTABLE_NAME).read_bytes() == b"old"


def test_a_broken_archive_is_reported(tmp_path):
    broken = tmp_path / "scrcpy.zip"
    broken.write_bytes(b"not a zip")

    with pytest.raises(ScrcpyInstallError, match="could not be unpacked"):
        install_archive(broken, tmp_path / "scrcpy")
