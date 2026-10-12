"""Download and install scrcpy from its GitHub releases.

The toolkit keeps its own copy in `paths.scrcpy_dir()`. `Scrcpy.find()` prefers that copy
over PATH, so a fresh install is used the next time a mirror window starts.
"""

import hashlib
import json
import platform
import shutil
import sys
import tarfile
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from adb_toolkit.config import APP_VERSION, SCRCPY_RELEASES_API_URL
from adb_toolkit.core import paths
from adb_toolkit.core.platform_tools import CHUNK_SIZE, ProgressCallback
from adb_toolkit.core.process import run
from adb_toolkit.core.scrcpy import EXECUTABLE_NAME
from adb_toolkit.core.versions import Version, parse_release_tag, parse_scrcpy_version

_ARCHIVE_SUFFIXES = (".zip", ".tar.gz")
_SUMS_FILE = "SHA256SUMS.txt"


class ScrcpyInstallError(RuntimeError):
    """The release could not be read, downloaded, verified or unpacked."""


@dataclass(frozen=True)
class RemoteScrcpy:
    version: Version
    url: str
    size: int
    sha256: str  # empty when the release gives no checksum for this build

    @property
    def file_name(self) -> str:
        return self.url.rsplit("/", 1)[-1]


@dataclass
class _Asset:
    name: str
    url: str
    size: int
    sha256: str


def asset_prefix(sys_platform: str, machine: str) -> str | None:
    """The start of the archive name scrcpy publishes for this system, or None when there is none."""
    machine = machine.lower()
    arm = machine in ("arm64", "aarch64")
    if sys_platform == "win32":
        if arm:
            return "scrcpy-winarm64-"
        return "scrcpy-win64-" if machine in ("amd64", "x86_64") else "scrcpy-win32-"
    if sys_platform == "darwin":
        return "scrcpy-macos-aarch64-" if arm else "scrcpy-macos-x86_64-"
    if sys_platform.startswith("linux") and machine in ("x86_64", "amd64"):
        return "scrcpy-linux-x86_64-"
    return None


def parse_release(body: str, sys_platform: str, machine: str) -> tuple[RemoteScrcpy, str | None]:
    """Pick this system's build out of GitHub's latest-release JSON.

    Returns the build and the URL of the release's checksum file, which is only needed when
    the build has no checksum of its own.
    """
    try:
        data = json.loads(body)
    except ValueError as error:
        raise ScrcpyInstallError(f"GitHub sent a scrcpy release that is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ScrcpyInstallError("GitHub sent a scrcpy release in an unexpected shape.")

    tag = str(data.get("tag_name") or "")
    version = parse_release_tag(tag)
    if version is None:
        raise ScrcpyInstallError(f"The latest scrcpy release has no readable version number: {tag!r}")
    prefix = asset_prefix(sys_platform, machine)
    if prefix is None:
        raise ScrcpyInstallError(f"scrcpy publishes no build for '{sys_platform}' on '{machine}'.")

    assets = [_asset(item) for item in data.get("assets") or [] if isinstance(item, dict)]
    chosen = next((a for a in assets if a.name.startswith(prefix) and a.name.endswith(_ARCHIVE_SUFFIXES)), None)
    if chosen is None:
        raise ScrcpyInstallError(f"scrcpy {version} has no download for '{sys_platform}' on '{machine}'.")
    sums = next((a.url for a in assets if a.name == _SUMS_FILE), None)
    return RemoteScrcpy(version, chosen.url, chosen.size, chosen.sha256), sums


def _asset(item: dict) -> _Asset:
    digest = str(item.get("digest") or "").lower()
    return _Asset(
        name=str(item.get("name") or ""),
        url=str(item.get("browser_download_url") or ""),
        size=int(item.get("size") or 0),
        sha256=digest.removeprefix("sha256:") if digest.startswith("sha256:") else "",
    )


def checksum_from_sums(sums_text: str, file_name: str) -> str:
    """Find a file's SHA-256 in the text of a `sha256sum` listing. Empty when it is not listed."""
    for line in sums_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == file_name:
            return parts[0].lower()
    return ""


def _open(url: str, timeout: float):
    if not url.startswith("https://"):
        raise ScrcpyInstallError(f"Refusing to download from a non-HTTPS address: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": f"ADB-Toolkit/{APP_VERSION}"})
    return urllib.request.urlopen(request, timeout=timeout)


def fetch_latest(timeout: float = 20, sys_platform: str = sys.platform, machine: str | None = None) -> RemoteScrcpy:
    """Ask GitHub for the newest scrcpy release and pick the build for this computer."""
    try:
        with _open(SCRCPY_RELEASES_API_URL, timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise ScrcpyInstallError(f"GitHub answered {error.code} when asked for the latest scrcpy.") from error
    except OSError as error:
        raise ScrcpyInstallError(f"Could not reach GitHub: {error}") from error

    remote, sums_url = parse_release(body, sys_platform, machine or platform.machine())
    if remote.sha256 or sums_url is None:
        return remote
    try:
        with _open(sums_url, timeout) as response:
            sums_text = response.read().decode("utf-8", errors="replace")
    except OSError as error:
        raise ScrcpyInstallError(f"Could not read the scrcpy checksums: {error}") from error
    return RemoteScrcpy(remote.version, remote.url, remote.size, checksum_from_sums(sums_text, remote.file_name))


def installed_version(executable: Path) -> Version | None:
    """The version of an installed scrcpy, or None when it is missing or does not answer."""
    if not executable.is_file():
        return None
    return parse_scrcpy_version(run([str(executable), "--version"], timeout=10).output)


def download(remote: RemoteScrcpy, destination: Path, progress: ProgressCallback | None = None) -> None:
    """Save the archive to `destination` and check its SHA-256. A download with no known checksum is refused."""
    if not remote.sha256:
        raise ScrcpyInstallError("The release gives no checksum for this download, so it was not installed.")
    digest = hashlib.sha256()
    received = 0
    try:
        with _open(remote.url, 30) as response, destination.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if progress is not None:
                    progress(received, remote.size)
    except OSError as error:
        raise ScrcpyInstallError(f"Download failed: {error}") from error

    if digest.hexdigest() != remote.sha256:
        destination.unlink(missing_ok=True)
        raise ScrcpyInstallError("The download did not match scrcpy's SHA-256 checksum. Try again.")


def install_archive(archive_path: Path, target: Path) -> Path:
    """Unpack a scrcpy archive and put the folder that holds the program at `target`.

    The old copy is kept until the new one is in place, so a failed update leaves a working scrcpy.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="extract-", dir=target.parent) as staging_name:
        staging = Path(staging_name)
        try:
            if archive_path.name.endswith(".zip"):
                with zipfile.ZipFile(archive_path) as archive:
                    archive.extractall(staging)
            else:
                with tarfile.open(archive_path) as archive:
                    archive.extractall(staging, filter="data")
        except (zipfile.BadZipFile, tarfile.TarError, OSError) as error:
            raise ScrcpyInstallError(f"The archive could not be unpacked: {error}") from error

        program = next((path for path in staging.rglob(EXECUTABLE_NAME) if path.is_file()), None)
        if program is None:
            raise ScrcpyInstallError(f"The archive does not contain {EXECUTABLE_NAME}.")
        source = program.parent

        previous = target.with_name(target.name + ".previous")
        shutil.rmtree(previous, ignore_errors=True)
        try:
            if target.exists():
                target.rename(previous)
            shutil.move(str(source), str(target))
        except OSError as error:
            if previous.exists() and not target.exists():
                previous.rename(target)
            raise ScrcpyInstallError(
                f"Could not replace the existing scrcpy. Close its windows and try again: {error}"
            ) from error
        shutil.rmtree(previous, ignore_errors=True)
    return target


_install_lock = threading.Lock()


def install(remote: RemoteScrcpy, progress: ProgressCallback | None = None) -> Path:
    """Download this release of scrcpy and install it. Installs are serialised, like platform-tools."""
    with _install_lock, tempfile.TemporaryDirectory(prefix="download-", dir=paths.data_dir()) as download_dir:
        archive_path = Path(download_dir) / remote.file_name
        download(remote, archive_path, progress)
        return install_archive(archive_path, paths.scrcpy_dir())
