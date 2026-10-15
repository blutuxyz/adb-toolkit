"""Files: install an APK on the selected phone, and copy files between this computer and the phone."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.adb import install_succeeded
from adb_toolkit.core.process import CommandResult
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    RADIUS_CONTROL,
    SCROLL_PADDING,
    SECTION_GAP,
    SPACE_M,
    TYPE_CAPTION,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import ONE_LINE, ProgressLine, button, card, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

DEFAULT_PHONE_FOLDER = "/sdcard/Download/"


class FilesView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._apk: str | None = None
        self._local: str | None = None
        self._apk_name = text("", size=TYPE_CAPTION, mono=True, color=colors.muted, **ONE_LINE)
        self._local_name = text("", size=TYPE_CAPTION, mono=True, color=colors.muted, **ONE_LINE)
        self._hint = text("", color=colors.muted)
        self._send_to = _path_field(DEFAULT_PHONE_FOLDER, "/sdcard/Download/")
        self._get_from = _path_field("", "/sdcard/DCIM/Camera/photo.jpg")
        self._progress = ProgressLine()

        self._choose_apk = button("outlined", t("Choose APK"), icon=ft.Icons.FOLDER_OPEN,
                                  on_click=lambda _: self.window.page.run_task(self._pick_apk))
        self._install_button = button("filled", t("Install"), icon=ft.Icons.INSTALL_MOBILE,
                                      on_click=lambda _: self.window.page.run_task(self._install))
        self._choose_file = button("outlined", t("Choose file"), icon=ft.Icons.FOLDER_OPEN,
                                   on_click=lambda _: self.window.page.run_task(self._pick_local))
        self._send_button = button("filled", t("Send"), icon=ft.Icons.UPLOAD,
                                   on_click=lambda _: self.window.page.run_task(self._send))
        self._get_button = button("filled", t("Choose folder and get"), icon=ft.Icons.DOWNLOAD,
                                  on_click=lambda _: self.window.page.run_task(self._get))

        self.body = ft.ListView(
            [
                card(
                    t("Install an app"),
                    [
                        _row(self._choose_apk, self._apk_name),
                        self._install_button,
                    ],
                    description=t("Install an APK file on the selected phone. Its data is kept."),
                    icon=ft.Icons.INSTALL_MOBILE,
                    hue="blue",
                ),
                card(
                    t("Send a file to the phone"),
                    [
                        _row(self._choose_file, self._local_name),
                        _caption(t("Folder on the phone")),
                        self._send_to,
                        self._send_button,
                    ],
                    description=t("Copies a file from this computer to the phone."),
                    icon=ft.Icons.UPLOAD,
                    hue="amber",
                ),
                card(
                    t("Get a file from the phone"),
                    [
                        _caption(t("File on the phone")),
                        self._get_from,
                        self._get_button,
                    ],
                    description=t("Copies a file from the phone to a folder you choose."),
                    icon=ft.Icons.DOWNLOAD,
                    hue="amber",
                ),
                self._progress.control,
                ft.Container(content=self._hint),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(
            t("Files"),
            self.body,
            subtitle=t("Install apps and copy files between this computer and the selected phone."),
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            hue="amber",
        )

    async def activate(self) -> None:
        self._paint()

    def _paint(self) -> None:
        ready = self._ready()
        busy = self.window.busy
        self._install_button.disabled = not ready or busy or self._apk is None
        self._send_button.disabled = not ready or busy or self._local is None
        self._get_button.disabled = not ready or busy
        self._choose_apk.disabled = busy
        self._choose_file.disabled = busy
        self._apk_name.value = Path(self._apk).name if self._apk else t("No file chosen")
        self._local_name.value = Path(self._local).name if self._local else t("No file chosen")
        self._hint.value = "" if ready else t("Connect a phone with USB debugging on to use these.")
        self.window.update()

    async def _pick_apk(self) -> None:
        chosen = await self.window.pick_files(title=t("Choose an APK"), extensions=["apk"])
        if chosen:
            self._apk = chosen[0]
        self._paint()

    async def _pick_local(self) -> None:
        chosen = await self.window.pick_files(title=t("Choose a file to send"), extensions=None)
        if chosen:
            self._local = chosen[0]
        self._paint()

    async def _install(self) -> None:
        serial, apk = self._serial(), self._apk
        if serial is None or apk is None:
            return
        name = Path(apk).name
        result = await self._job(t("Installing {name}", name=name), self.window.session.adb.install_apk, serial, apk)

        if install_succeeded(result.output):
            self.window.notify(t("Installed {name}", name=name), success=True)
        else:
            self.window.notify(result.output or t("The install did not finish."), error=True)

    async def _send(self) -> None:
        serial, local = self._serial(), self._local
        remote = _phone_path(self._send_to.value)
        if serial is None or local is None:
            return
        if remote is None:
            self.window.notify(t("The phone path must start with /."), error=True)
            return
        name = Path(local).name
        result = await self._job(t("Sending {name}", name=name), self.window.session.adb.push, serial, local, remote)
        if result.ok:
            self.window.notify(t("Sent {name} to the phone.", name=name), success=True)
        else:
            self.window.notify(result.output or t("The transfer did not finish."), error=True)

    async def _get(self) -> None:
        serial = self._serial()
        remote = _phone_path(self._get_from.value)
        if serial is None:
            return
        if remote is None:
            self.window.notify(t("The phone path must start with /."), error=True)
            return
        folder = await self.window.pick_folder(t("Choose where to save the file"))
        if not folder:
            return
        name = PurePosixPath(remote).name
        local = str(Path(folder) / name)
        result = await self._job(t("Getting {name}", name=name), self.window.session.adb.pull, serial, remote, local)
        if result.ok:
            self.window.notify(t("Saved {name} to {folder}", name=name, folder=folder), success=True)
        else:
            self.window.notify(result.output or t("The transfer did not finish."), error=True)

    async def _job(self, label: str, func, *args) -> CommandResult:
        """Run one command with the progress line shown, and return its result."""
        self._progress.start(label)
        self._paint()
        try:
            return await self.window.run_job(func, *args, on_line=self._progress.feed, on_tick=self._progress.tick)
        finally:
            self._progress.hide()
            self._paint()

    def _ready(self) -> bool:
        device = self.window.session.selected_device
        return device is not None and device.is_ready

    def _serial(self) -> str | None:
        device = self.window.session.selected_device
        return device.serial if device is not None and device.is_ready else None


def _path_field(value: str, hint: str) -> ft.TextField:
    colors = palette()
    return ft.TextField(
        value=value,
        hint_text=hint,
        height=CONTROL_HEIGHT,
        border_radius=RADIUS_CONTROL,
        border_color=colors.control_border,
        focused_border_color=colors.accent,
        cursor_color=colors.accent,
    )


def _caption(label: str) -> ft.Text:
    return text(label, size=TYPE_CAPTION, color=palette().muted)


def _row(action: ft.Control, name: ft.Control) -> ft.Row:
    return ft.Row(
        [action, ft.Container(expand=True, content=name)],
        spacing=SPACE_M,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _phone_path(value: str | None) -> str | None:
    """A path on the phone. It must be absolute, because adb resolves nothing else on Android."""
    path = (value or "").strip()
    return path if path.startswith("/") and len(path) > 1 else None
