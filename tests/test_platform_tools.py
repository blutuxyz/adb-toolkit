import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pytest

from adb_toolkit.core import platform_tools
from adb_toolkit.core.platform_tools import PlatformToolsError, download, install_archive
from adb_toolkit.core.updates import RemoteArchive


def _exe(name: str) -> str:
    return f"{name}.exe" if sys.platform == "win32" else name


def _make_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


def _platform_tools_zip(path: Path, marker: bytes) -> Path:
    return _make_zip(
        path,
        {
            f"platform-tools/{_exe('adb')}": marker,
            f"platform-tools/{_exe('fastboot')}": marker,
            "platform-tools/source.properties": b"Pkg.Revision=37.0.1\n",
        },
    )


def test_install_unpacks_the_tools_into_the_target_folder(tmp_path):
    zip_path = _platform_tools_zip(tmp_path / "pt.zip", b"new")
    target = tmp_path / "data" / "platform-tools"

    installed = install_archive(zip_path, target)

    assert installed == target
    assert (target / _exe("adb")).read_bytes() == b"new"
    assert (target / _exe("fastboot")).read_bytes() == b"new"
    assert not (target.parent / "platform-tools.previous").exists()


def test_reinstall_replaces_the_old_copy_completely(tmp_path):
    target = tmp_path / "platform-tools"
    target.mkdir()
    (target / "stale-file.txt").write_text("old")
    (target / _exe("adb")).write_bytes(b"old")

    install_archive(_platform_tools_zip(tmp_path / "pt.zip", b"new"), target)

    assert not (target / "stale-file.txt").exists()
    assert (target / _exe("adb")).read_bytes() == b"new"


def test_archive_without_adb_is_rejected_and_leaves_nothing_behind(tmp_path):
    zip_path = _make_zip(tmp_path / "bad.zip", {"readme.txt": b"nothing useful"})
    target = tmp_path / "platform-tools"

    with pytest.raises(PlatformToolsError, match="adb"):
        install_archive(zip_path, target)

    assert not target.exists()


def test_archive_missing_fastboot_is_rejected(tmp_path):
    zip_path = _make_zip(tmp_path / "half.zip", {f"platform-tools/{_exe('adb')}": b"x"})

    with pytest.raises(PlatformToolsError, match="fastboot"):
        install_archive(zip_path, tmp_path / "platform-tools")


def test_download_saves_the_file_when_the_checksum_matches(tmp_path, monkeypatch):
    payload = b"platform-tools bytes" * 1000
    archive = RemoteArchive(
        url="https://example.test/pt.zip",
        size=len(payload),
        sha1=hashlib.sha1(payload).hexdigest(),
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(payload))
    progress_calls = []

    destination = tmp_path / "pt.zip"
    download(archive, destination, progress=lambda done, total: progress_calls.append((done, total)))

    assert destination.read_bytes() == payload
    assert progress_calls[-1] == (len(payload), len(payload))


def test_download_with_wrong_checksum_is_deleted_and_reported(tmp_path, monkeypatch):
    payload = b"tampered"
    archive = RemoteArchive(url="https://example.test/pt.zip", size=len(payload), sha1="0" * 40)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(payload))
    destination = tmp_path / "pt.zip"

    with pytest.raises(PlatformToolsError, match="checksum"):
        download(archive, destination)

    assert not destination.exists()


def test_download_network_error_becomes_a_platform_tools_error(tmp_path, monkeypatch):
    def offline(*args, **kwargs):
        raise urllib.error.URLError("no route to host")

    archive = RemoteArchive(url="https://example.test/pt.zip", size=1, sha1="0" * 40)
    monkeypatch.setattr(urllib.request, "urlopen", offline)

    with pytest.raises(PlatformToolsError, match="Download failed"):
        download(archive, tmp_path / "pt.zip")


def test_find_tool_prefers_our_copy_when_it_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_tools.paths, "platform_tools_dir", lambda: tmp_path)
    (tmp_path / _exe("adb")).write_bytes(b"x")

    assert platform_tools.find_tool("adb") == str(tmp_path / _exe("adb"))
