"""Apps: every package on the selected phone, with uninstall and restore."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.adb import AdbError
from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.core.packages import SYSTEM, USER, AppEntry, restore_succeeded, uninstall_succeeded
from adb_toolkit.ui.dialogs import confirm
from adb_toolkit.ui.theme import CONTROL_HEIGHT, ROW_PADDING, SECTION_GAP, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import empty_state, hairline, letter_tile, text, title_block

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

FILTERS = (("all", "All"), ("user", "User"), ("system", "System"), ("removed", "Removed"))

class AppsView(View):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        colors = palette()
        self._entries: list[AppEntry] = []
        self._loaded_serial: str | None = None
        self._pending: str | None = None
        self._filter = "all"
        self._query = ""

        self._search = ft.TextField(
            hint_text="Search packages",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            height=CONTROL_HEIGHT,
            border_radius=CONTROL_HEIGHT / 2,
            border_color=colors.line,
            focused_border_color=colors.accent,
            cursor_color=colors.accent,
            on_change=self._on_query,
        )
        self._filters = ft.SegmentedButton(
            selected=[self._filter],
            segments=[
                ft.Segment(value=value, label=text(label, size=13, no_wrap=True)) for value, label in FILTERS
            ],
            on_change=self._on_filter,
        )
        self._count = text("", size=13, color=colors.muted)
        self._list = ft.ListView(expand=True, spacing=0, padding=ft.Padding.only(right=8))
        self._body = ft.Container(expand=True, content=self._list)

        self._toolbar = ft.Row(
            [
                self._search,
                self._filters,
                ft.Container(expand=True),
                self._count,
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Reload packages",
                    icon_color=colors.muted,
                    on_click=lambda _: self.window.page.run_task(self.activate),
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.control = ft.Column(
            [
                title_block("Apps"),
                ft.Container(height=SECTION_GAP),
                self._toolbar,
                ft.Container(height=8),
                hairline(),
                self._body,
            ],
            expand=True,
            spacing=0,
        )

    async def activate(self) -> None:
        device = self.window.session.selected_device
        self._loaded_serial = device.serial if device else None
        if device is None or not device.is_ready:
            self._entries = []
            self._show_message(*_not_ready_message(device))
            return

        self._show_message("", "Loading packages", "", spinner=True)
        try:
            self._entries = await self.window.run_blocking(
                self.window.session.adb.list_packages, device.serial
            )
        except AdbError as error:
            self._entries = []
            self._show_message(ft.Icons.ERROR_OUTLINE, "Could not list packages", str(error), "danger")
            return
        self._render()

    async def on_devices_changed(self) -> None:
        device = self.window.session.selected_device
        if (device.serial if device else None) != self._loaded_serial:
            await self.activate()

    def _on_query(self, event: ft.ControlEvent) -> None:
        typed = event.data if isinstance(event.data, str) else event.control.value
        self._query = (typed or "").strip().lower()
        self._render()

    def _on_filter(self, event: ft.ControlEvent) -> None:
        # The new selection arrives in event.data. The control's own list is not updated yet.
        chosen = json.loads(event.data) if isinstance(event.data, str) else event.data
        self._filter = next(iter(chosen or []), "all")
        self._filters.selected = [self._filter]
        self._render()

    def _matches(self, entry: AppEntry) -> bool:
        if self._query and self._query not in entry.package.lower():
            return False
        return {
            "all": True,
            "user": entry.kind == USER,
            "system": entry.kind == SYSTEM and entry.installed,
            "removed": entry.removed,
        }[self._filter]

    def _render(self) -> None:
        visible = [entry for entry in self._entries if self._matches(entry)]
        if not visible:
            self._show_message(
                ft.Icons.SEARCH_OFF,
                "No packages match",
                "",
                toolbar=True,
            )
            self._count.value = f"0 of {len(self._entries)}"
            self.window.update()
            return

        rows: list[ft.Control] = []
        for index, entry in enumerate(visible):
            if index:
                rows.append(hairline())
            rows.append(self._row(entry))
        self._list.controls = rows
        self._body.content = self._list
        self._toolbar.visible = True
        total = len(self._entries)
        self._count.value = f"{total} packages" if len(visible) == total else f"{len(visible)} of {total}"
        self.window.update()

    def _row(self, entry: AppEntry) -> ft.Container:
        colors = palette()
        if self._pending == entry.package:
            action: ft.Control = ft.ProgressRing(width=18, height=18, stroke_width=2)
        elif entry.removed:
            action = ft.FilledTonalButton(
                content=text("Restore app"),
                icon=ft.Icons.RESTORE,
                icon_color=colors.green,
                disabled=self._pending is not None,
                on_click=lambda _, item=entry: self.window.page.run_task(self._restore, item),
            )
        else:
            action = ft.TextButton(
                content=text("Uninstall", color=colors.danger),
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=colors.danger,
                disabled=self._pending is not None,
                on_click=lambda _, item=entry: self._confirm_uninstall(item),
            )

        return ft.Container(
            padding=ft.Padding.symmetric(vertical=ROW_PADDING),
            content=ft.Row(
                [
                    letter_tile(entry.package),
                    ft.Column(
                        [
                            text(entry.package, size=14, mono=True),
                            text(entry.tag, size=12, color=colors.muted),
                        ],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    action,
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _show_message(
        self, icon: str, title: str, body: str, hue: str = "blue", *, spinner: bool = False, toolbar: bool = False
    ) -> None:
        """Replace the list with a message. The toolbar stays only when the user can act on it."""
        state = empty_state(title, body, icon=icon, hue=hue, spinner=spinner)
        self._body.content = ft.Container(padding=ft.Padding.only(top=48), content=state)
        self._count.value = ""
        self._toolbar.visible = toolbar
        self.window.update()

    def _confirm_uninstall(self, entry: AppEntry) -> None:
        if entry.kind == SYSTEM:
            message = "Removed for this user only. Its data stays on the phone."
        else:
            message = "The app and its data are deleted."
        confirm(
            self.window.page,
            title=f"Uninstall {entry.package}?",
            message=message,
            action_label="Uninstall",
            destructive=True,
            icon=ft.Icons.DELETE_OUTLINE,
            hue="danger",
            on_confirm=lambda: self.window.page.run_task(self._uninstall, entry),
        )

    async def _uninstall(self, entry: AppEntry) -> None:
        serial = self._serial()
        if serial is None:
            return
        self._pending = entry.package
        self._render()
        try:
            result = await self.window.run_blocking(
                self.window.session.adb.uninstall, serial, entry.package, system=entry.kind == SYSTEM
            )
        finally:
            self._pending = None
            self._render()
        if uninstall_succeeded(result.output):
            self.window.notify(f"Uninstalled {entry.package}", success=True)
            await self.activate()
        else:
            self.window.notify(result.output or "The uninstall did not finish.", error=True)
            self._render()

    async def _restore(self, entry: AppEntry) -> None:
        serial = self._serial()
        if serial is None:
            return
        self._pending = entry.package
        self._render()
        try:
            result = await self.window.run_blocking(self.window.session.adb.restore, serial, entry.package)
        finally:
            self._pending = None
            self._render()
        if restore_succeeded(result.output):
            self.window.notify(f"Restored {entry.package}", success=True)
            await self.activate()
        else:
            self.window.notify(result.output or "The restore did not finish.", error=True)
            self._render()

    def _serial(self) -> str | None:
        device = self.window.session.selected_device
        return device.serial if device and device.is_ready else None


def _not_ready_message(device: Device | None) -> tuple[str, str, str, str]:
    """Icon, title, body and hue for the list area when there is no ready device to read from."""
    if device is None:
        return (
            ft.Icons.PHONE_ANDROID,
            "No device connected",
            "Connect a phone with USB debugging on.",
            "blue",
        )
    if device.mode == FASTBOOT:
        return (
            ft.Icons.FLASH_ON,
            "The phone is in fastboot mode",
            "Reboot to Android to manage apps.",
            "violet",
        )
    if device.state == "unauthorized":
        return (
            ft.Icons.LOCK_OUTLINE,
            "Allow USB debugging on the phone",
            "Accept the prompt on the phone.",
            "amber",
        )
    return (
        ft.Icons.USB_OFF,
        f"The device is {device.state}",
        "Reconnect the cable.",
        "danger",
    )
