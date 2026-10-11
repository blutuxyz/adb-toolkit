"""Find the latest platform-tools release in Google's SDK repository feed."""

import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from adb_toolkit.config import PLATFORM_TOOLS_BASE_URL, PLATFORM_TOOLS_REPOSITORY_URL
from adb_toolkit.core.versions import Version

# Maps sys.platform to the host-os value Google uses in the feed.
HOST_OS_BY_PLATFORM = {"win32": "windows", "darwin": "macosx", "linux": "linux"}


class UpdateError(RuntimeError):
    """The feed could not be read, or it has no build for this operating system."""


@dataclass(frozen=True)
class RemoteArchive:
    url: str
    size: int
    sha1: str

    @property
    def file_name(self) -> str:
        return urlparse(self.url).path.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class RemotePlatformTools:
    version: Version
    archives: dict[str, RemoteArchive] = field(default_factory=dict)

    def archive_for(self, platform: str) -> RemoteArchive:
        host_os = HOST_OS_BY_PLATFORM.get(platform)
        archive = self.archives.get(host_os) if host_os else None
        if archive is None:
            raise UpdateError(f"No platform-tools build is published for '{platform}'.")
        return archive


def parse_platform_tools(feed_xml: str, base_url: str = PLATFORM_TOOLS_BASE_URL) -> RemotePlatformTools:
    """Read the platform-tools entry from the SDK repository XML."""
    try:
        root = ET.fromstring(feed_xml)
    except ET.ParseError as error:
        raise UpdateError(f"The SDK repository feed is not valid XML: {error}") from error

    for package in root.iter("remotePackage"):
        if package.get("path") != "platform-tools":
            continue
        revision = package.find("revision")
        if revision is None:
            raise UpdateError("The platform-tools entry has no revision.")
        version = Version(
            int(revision.findtext("major", "0")),
            int(revision.findtext("minor", "0")),
            int(revision.findtext("micro", "0")),
        )
        archives: dict[str, RemoteArchive] = {}
        for archive in package.iter("archive"):
            host_os = archive.findtext("host-os")
            complete = archive.find("complete")
            if not host_os or complete is None:
                continue
            archives[host_os] = RemoteArchive(
                url=urljoin(base_url, complete.findtext("url", "")),
                size=int(complete.findtext("size", "0")),
                sha1=(complete.findtext("checksum") or "").strip(),
            )
        return RemotePlatformTools(version=version, archives=archives)

    raise UpdateError("platform-tools is missing from the SDK repository feed.")


def fetch_latest(timeout: float = 20) -> RemotePlatformTools:
    """Download the SDK repository feed and return the latest platform-tools entry."""
    try:
        with urllib.request.urlopen(PLATFORM_TOOLS_REPOSITORY_URL, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except OSError as error:
        raise UpdateError(f"Could not reach Google's SDK repository: {error}") from error
    return parse_platform_tools(body)
