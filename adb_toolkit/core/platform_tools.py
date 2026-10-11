"""Install and update Google's platform-tools (adb and fastboot)."""

import hashlib
import os
import shutil
import sys
import tempfile
import threading
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from adb_toolkit.core import paths
from adb_toolkit.core.process import run
from adb_toolkit.core.updates import RemoteArchive, RemotePlatformTools
from adb_toolkit.core.versions import Version, parse_tool_version

# Called as progress(bytes_received, bytes_total) while a download runs.
ProgressCallback = Callable[[int, int], None]

CHUNK_SIZE = 64 * 1024
REQUIRED_TOOLS = ("adb", "fastboot")


class PlatformToolsError(RuntimeError):
    """A download, checksum or installation step failed."""


@dataclass
class Progress:
    """Latest download numbers. The worker thread writes them and the UI reads them."""

    done: int = 0
    total: int = 0


def _binary(name: str) -> str:
    return f"{name}.exe" if sys.platform == "win32" else name


def managed_binary(name: str) -> Path:
    """Path to our copy of a tool. It may not exist yet."""
    return paths.platform_tools_dir() / _binary(name)


def find_tool(name: str) -> str:
    """Our copy of a tool if it is installed, otherwise whatever PATH provides."""
    managed = managed_binary(name)
    if managed.is_file():
        return str(managed)
    return shutil.which(name) or name


@dataclass(frozen=True)
class LocalInstall:
    installed: bool
    adb_version: Version | None = None
    fastboot_version: Version | None = None


def local_install() -> LocalInstall:
    """Check whether both tools are present and read their versions."""
    adb, fastboot = managed_binary("adb"), managed_binary("fastboot")
    if not (adb.is_file() and fastboot.is_file()):
        return LocalInstall(installed=False)
    return LocalInstall(
        installed=True,
        adb_version=parse_tool_version(run([str(adb), "version"], timeout=10).output),
        fastboot_version=parse_tool_version(run([str(fastboot), "--version"], timeout=10).output),
    )


def download(archive: RemoteArchive, destination: Path, progress: ProgressCallback | None = None) -> None:
    """Save the archive to `destination` and check its SHA-1 against the feed."""
    digest = hashlib.sha1()
    received = 0
    try:
        with urllib.request.urlopen(archive.url, timeout=30) as response, destination.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if progress is not None:
                    progress(received, archive.size)
    except OSError as error:
        raise PlatformToolsError(f"Download failed: {error}") from error

    if digest.hexdigest() != archive.sha1:
        destination.unlink(missing_ok=True)
        raise PlatformToolsError("The download did not match Google's SHA-1 checksum. Try again.")


def install_archive(zip_path: Path, target: Path) -> Path:
    """Unpack a platform-tools zip and put its contents at `target`.

    The old copy is kept until the new one is in place, so a failed update
    does not leave the user without tools.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="extract-", dir=target.parent) as staging_name:
        staging = Path(staging_name)
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(staging)
        except (zipfile.BadZipFile, OSError) as error:
            raise PlatformToolsError(f"The archive could not be unpacked: {error}") from error

        adb = next(staging.rglob(_binary("adb")), None)
        if adb is None:
            raise PlatformToolsError("The archive does not contain adb.")
        source = adb.parent
        for name in REQUIRED_TOOLS:
            if not (source / _binary(name)).is_file():
                raise PlatformToolsError(f"The archive does not contain {name}.")
            if os.name == "posix":
                binary = source / _binary(name)
                binary.chmod(binary.stat().st_mode | 0o755)

        _stop_adb_server(target)
        previous = target.with_name(target.name + ".previous")
        shutil.rmtree(previous, ignore_errors=True)
        if target.exists():
            target.rename(previous)
        try:
            shutil.move(str(source), str(target))
        except OSError as error:
            if previous.exists() and not target.exists():
                previous.rename(target)
            raise PlatformToolsError(f"Could not replace the existing tools: {error}") from error
        shutil.rmtree(previous, ignore_errors=True)
    return target


_install_lock = threading.Lock()


def install(remote: RemotePlatformTools, progress: ProgressCallback | None = None) -> Path:
    """Download the latest platform-tools for this OS and install them.

    Installs are serialised, so two requests cannot replace the same folder at once.
    """
    archive = remote.archive_for(sys.platform)
    with _install_lock, tempfile.TemporaryDirectory(prefix="download-", dir=paths.data_dir()) as download_dir:
        zip_path = Path(download_dir) / archive.file_name
        download(archive, zip_path, progress)
        return install_archive(zip_path, paths.platform_tools_dir())


def _stop_adb_server(folder: Path) -> None:
    """Stop a running adb server so its binary can be replaced on Windows."""
    adb = folder / _binary("adb")
    if adb.is_file():
        run([str(adb), "kill-server"], timeout=10)
