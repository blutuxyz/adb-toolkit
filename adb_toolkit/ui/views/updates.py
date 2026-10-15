"""Updates: adb and fastboot against Google's latest platform-tools, and ADB Toolkit against its latest GitHub release."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.config import APP_VERSION, PROJECT_URL
from adb_toolkit.core.platform_tools import Progress, managed_binary
from adb_toolkit.core.versions import Version
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    ICON_ROW,
    ROW_PADDING,
    SCROLL_PADDING,
    SECTION_GAP,
    SPACE_M,
    SPACE_S,
    TYPE_CAPTION,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import StatusLine, button, card, icon_tile, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


class UpdatesView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._error = text("", color=colors.danger, strong=True)
        self._progress = ft.ProgressBar(value=0, visible=False, color=colors.accent, bgcolor=colors.panel_high,
                                        bar_height=6)
        self._progress_text = text("", size=TYPE_CAPTION, color=colors.muted)
        self._check = button(
            "outlined",
            t("Check for updates"),
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self.window.page.run_task(self._check_for_updates),
        )

        # Each status line is set from the session; its button only appears when there is something to do.
        self._tools = StatusLine()
        self._adb_version = text("", mono=True)
        self._fastboot_version = text("", mono=True)
        self._install = button(
            "filled",
            t("Install update"),
            icon=ft.Icons.DOWNLOAD,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self._install_update),
        )

        self._app = StatusLine()
        self._app_button = button(
            "outlined",
            t("Release page"),
            icon=ft.Icons.OPEN_IN_NEW,
            visible=False,
            on_click=lambda _: self.window.page.run_task(self._open_app_release),
        )

        platform_rows = [
            _status_block(self._tools),
            _tool_row("adb", str(managed_binary("adb").parent), self._adb_version, ft.Icons.TERMINAL, "green"),
            _tool_row(
                "fastboot",
                str(managed_binary("fastboot").parent),
                self._fastboot_version,
                ft.Icons.FLASH_ON,
                "violet",
            ),
        ]
        app_rows = [
            _status_block(self._app),
            _tool_row(
                "ADB Toolkit",
                PROJECT_URL.removeprefix("https://"),
                text(APP_VERSION, mono=True),
                ft.Icons.APPS,
                "blue",
            ),
        ]
        self.body = ft.ListView(
            [
                card(
                    "Platform-tools",
                    platform_rows,
                    description=t("Google's adb and fastboot, from the SDK feed."),
                    action=self._install,
                    icon=ft.Icons.DEVELOPER_BOARD,
                    hue="green",
                    divided=True,
                ),
                card(
                    "ADB Toolkit",
                    app_rows,
                    description=t("This app, from its latest GitHub release."),
                    action=self._app_button,
                    icon=ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED,
                    hue="accent",
                    divided=True,
                ),
                ft.Column([self._progress, self._progress_text, self._error], spacing=SPACE_S, tight=True),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(
            t("Updates"),
            self.body,
            subtitle=t("Check the platform-tools and this app against their latest releases."),
            icon=ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED,
            hue="accent",
            actions=[self._check],
        )

    async def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Redraw the versions and both update statuses from the session."""
        session = self.window.session
        self._adb_version.value = _version_text(session.local.adb_version)
        self._fastboot_version.value = _version_text(session.local.fastboot_version)
        self._error.value = ""
        self._paint_platform_tools()
        self._paint_app()
        self.window.update()

    def _paint_platform_tools(self) -> None:
        session = self.window.session
        colors = palette()
        if session.latest is None:
            self._tools.set(t("Not checked yet"), colors.muted)
            _show_action(self._install, visible=False)
        elif session.update_available:
            self._tools.set(t("Update available: {version}", version=session.latest), colors.signal)
            _show_action(self._install, visible=True, label=t("Install {version}", version=session.latest), icon=ft.Icons.DOWNLOAD)
        else:
            self._tools.set(t("Up to date"), colors.accent)
            _show_action(self._install, visible=False)

    def _paint_app(self) -> None:
        session = self.window.session
        colors = palette()
        release = session.app_release
        if not session.app_checked:
            self._app.set(t("Not checked yet"), colors.muted)
            _show_action(self._app_button, visible=False)
        elif release is None:
            self._app.set(t("No release yet"), colors.muted)
            _show_action(self._app_button, visible=False)
        elif session.app_update_available:
            self._app.set(t("Update available: {version}", version=release.version), colors.signal)
            _show_action(
                self._app_button, visible=True, label=t("View {version}", version=release.version), icon=ft.Icons.OPEN_IN_NEW
            )
        else:
            self._app.set(t("Up to date"), colors.accent)
            _show_action(self._app_button, visible=False)

    def show_error(self, message: str) -> None:
        self._error.value = message
        self.window.update()

    async def _check_for_updates(self) -> None:
        self._set_busy(True)
        self._tools.set(t("Checking"), palette().muted)
        self._app.set(t("Checking"), palette().muted)
        self.window.update()
        error = await self.window.check_updates()
        self._set_busy(False)
        self.refresh()
        if error:
            self.show_error(error)

    async def _install_update(self) -> None:
        # Installing restarts the adb server, which would cut off a running transfer or sideload.
        if self.window.busy:
            self.window.notify(t("Wait for the running task to finish."), error=True)
            return
        self._set_busy(True)
        self._progress.visible = True
        self._progress.value = None
        self._progress_text.value = t("Downloading")
        self.window.update()

        def on_progress(progress: Progress) -> None:
            if progress.total:
                self._progress.value = progress.done / progress.total
                self._progress_text.value = (
                    t("{done} of {total} MB", done=f"{progress.done / 1_000_000:.1f}", total=f"{progress.total / 1_000_000:.1f}")
                )
            self.window.update()

        error = await self.window.install_platform_tools(on_progress)
        self._progress.visible = False
        self._progress_text.value = ""
        self._set_busy(False)
        self.refresh()
        if error:
            self.show_error(error)
        else:
            self.window.notify(t("Platform-tools updated."), success=True)

    async def _open_app_release(self) -> None:
        release = self.window.session.app_release
        if release is not None:
            await self.window.open_url(release.page_url)

    def _set_busy(self, busy: bool) -> None:
        self._check.disabled = busy
        self._install.disabled = busy
        self._app_button.disabled = busy
        self.window.update()


def _show_action(control: ft.Control, *, visible: bool, label: str = "", icon: str | None = None) -> None:
    """Show or hide an action button and set its label. The label is only set when the button is shown."""
    control.visible = visible
    if visible:
        control.content.value = label
        control.content.update()
        control.icon = icon


def _status_block(line: StatusLine) -> ft.Container:
    return ft.Container(padding=ft.Padding.only(top=ROW_PADDING, bottom=SPACE_S), content=line.control)


def _tool_row(name: str, location: str, version: ft.Text, icon: str, hue: str) -> ft.Container:
    """A line of a version table: the tool, where it lives in mono, and its version in mono on the right."""
    colors = palette()
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=ROW_PADDING),
        content=ft.Row(
            [
                icon_tile(icon, hue, size=ICON_ROW),
                ft.Column(
                    [
                        text(name, strong=True),
                        text(location, size=TYPE_CAPTION, mono=True, color=colors.muted),
                    ],
                    spacing=0,
                    tight=True,
                    expand=True,
                ),
                version,
            ],
            spacing=SPACE_M,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _version_text(version: Version | None) -> str:
    return str(version) if version else t("Not installed")
