import pytest

from adb_toolkit.core.updates import UpdateError, parse_platform_tools
from adb_toolkit.core.versions import Version

FEED = """<?xml version='1.0' encoding='utf-8'?>
<sdk-repository>
  <remotePackage path="build-tools;34.0.0">
    <revision><major>34</major><minor>0</minor><micro>0</micro></revision>
  </remotePackage>
  <remotePackage path="platform-tools">
    <revision>
      <major>37</major>
      <minor>0</minor>
      <micro>1</micro>
    </revision>
    <archives>
      <archive>
        <complete>
          <size>9054187</size>
          <checksum type="sha1">477254aa5f903c15cf51001717bdf347fb6b53e0</checksum>
          <url>platform-tools_r37.0.1-linux.zip</url>
        </complete>
        <host-os>linux</host-os>
      </archive>
      <archive>
        <complete>
          <size>8044989</size>
          <checksum type="sha1">e03e78b1d80b396f1c3358e31251cb31740e1110</checksum>
          <url>platform-tools_r37.0.1-win.zip</url>
        </complete>
        <host-os>windows</host-os>
      </archive>
    </archives>
  </remotePackage>
</sdk-repository>
"""


def test_reads_the_latest_platform_tools_revision():
    remote = parse_platform_tools(FEED)

    assert remote.version == Version(37, 0, 1)


def test_picks_the_archive_for_the_running_operating_system():
    remote = parse_platform_tools(FEED)

    archive = remote.archive_for("win32")

    assert archive.url == "https://dl.google.com/android/repository/platform-tools_r37.0.1-win.zip"
    assert archive.size == 8044989
    assert archive.sha1 == "e03e78b1d80b396f1c3358e31251cb31740e1110"
    assert archive.file_name == "platform-tools_r37.0.1-win.zip"


def test_maps_linux_to_its_own_archive():
    remote = parse_platform_tools(FEED)

    assert remote.archive_for("linux").file_name == "platform-tools_r37.0.1-linux.zip"


def test_unsupported_platform_is_an_error():
    remote = parse_platform_tools(FEED)

    with pytest.raises(UpdateError):
        remote.archive_for("freebsd13")


def test_feed_without_platform_tools_is_an_error():
    with pytest.raises(UpdateError):
        parse_platform_tools("<sdk-repository></sdk-repository>")


def test_broken_xml_is_an_error():
    with pytest.raises(UpdateError):
        parse_platform_tools("<sdk-repository>")
