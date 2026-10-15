"""Apps: every package on the selected phone, with uninstall and restore."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.adb import AdbError
from adb_toolkit.core.devices import FASTBOOT, Device
from adb_toolkit.core.packages import SYSTEM, USER, AppEntry, restore_succeeded, uninstall_succeeded
from adb_toolkit.ui.dialogs import confirm
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    ICON_ROW,
    RADIUS_CARD,
    RADIUS_PILL,
    ROW_PADDING,
    SCROLL_PADDING,
    SPACE_L,
    SPACE_M,
    SPACE_S,
    SPACE_XL,
    SPACE_XS,
    TYPE_BODY,
    TYPE_CAPTION,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import (
    PillGroup,
    button,
    empty_state,
    hairline,
    icon_tile,
    letter_hue,
    screen_frame,
    tag,
    text,
)

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

# The filter pills, as (value, English label).
FILTERS = (("all", "All"), ("user", "User"), ("system", "System"), ("removed", "Removed"))
# The icon for a package's tile, by what kind of package it is.
_KIND_ICONS = {USER: ft.Icons.ANDROID, SYSTEM: ft.Icons.SETTINGS_SUGGEST}


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
            hint_text=t("Search packages"),
            prefix_icon=ft.Icons.SEARCH,
            expand=True,  # takes what the count and the reload button leave
            height=CONTROL_HEIGHT,
            border_radius=RADIUS_PILL,
            border_color=colors.control_border,
            focused_border_color=colors.accent,
            cursor_color=colors.accent,
            on_change=self._on_query,
        )
        self._chips = PillGroup(
            tuple((value, t(label)) for value, label in FILTERS), self._filter, self._on_filter
        )
        self._count = text("", size=TYPE_CAPTION, color=colors.muted, strong=True)
        self._list = ft.ListView(expand=True, spacing=0, padding=SCROLL_PADDING)
        # The list sits in one bordered surface. Its content is replaced by a message when there is nothing to list.
        self._body = ft.Container(
            expand=True,
            bgcolor=colors.panel,
            border=ft.Border.all(1, colors.line),
            border_radius=RADIUS_CARD,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self._list,
        )

        self._search_row = ft.Row(
            [
                self._search,
                self._count,
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip=t("Reload packages"),
                    icon_color=colors.muted,
                    on_click=lambda _: self.window.page.run_task(self.activate),
                ),
            ],
            spacing=SPACE_M,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._toolbar = ft.Column([self._search_row, self._chips.control], spacing=SPACE_M, tight=True)

        self.control = screen_frame(
            t("Apps"),
            self._body,
            subtitle=t("Packages on the selected phone. Uninstalling removes an app for this user."),
            icon=ft.Icons.APPS_OUTLINED,
            hue="blue",
            toolbar=self._toolbar,
        )

    async def activate(self) -> None:
        device = self.window.session.selected_device
        self._loaded_serial = device.serial if device else None
        if device is None or not device.is_ready:
            self._entries = []
            self._show_message(*_not_ready_message(device))
            return

        self._show_message("", t("Loading packages"), "", spinner=True)
        try:
            self._entries = await self.window.run_blocking(
                self.window.session.adb.list_packages, device.serial
            )
        except AdbError as error:
            self._entries = []
            self._show_message(ft.Icons.ERROR_OUTLINE, t("Could not list packages"), str(error), "danger")
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

    def _on_filter(self, value: str) -> None:
        self._filter = value
        self._chips.select(value)
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
                t("No packages match"),
                "",
                toolbar=True,
            )
            self._count.value = t("0 of {total}", total=len(self._entries))
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
        if len(visible) == total:
            self._count.value = t("{total} packages", total=total)
        else:
            self._count.value = t("{shown} of {total}", shown=len(visible), total=total)
        self.window.update()

    def _row(self, entry: AppEntry) -> ft.Container:
        colors = palette()
        if self._pending == entry.package:
            action: ft.Control = ft.ProgressRing(width=18, height=18, stroke_width=2)
        elif entry.removed:
            action = button(
                "outlined",
                t("Restore"),
                icon=ft.Icons.RESTORE,
                disabled=self._pending is not None,
                on_click=lambda _, item=entry: self.window.page.run_task(self._restore, item),
            )
        else:
            action = button(
                "text_danger",
                t("Uninstall"),
                icon=ft.Icons.DELETE_OUTLINE,
                disabled=self._pending is not None,
                on_click=lambda _, item=entry: self._confirm_uninstall(item),
            )

        # A removed package has no install to tag, so its state goes on the line under the name.
        state: list[ft.Control] = [text(t(entry.tag), size=TYPE_CAPTION, color=colors.muted)]
        if entry.removed:
            state.append(tag(t("Removed"), colors.signal))
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE_L, vertical=ROW_PADDING),
            content=ft.Row(
                [
                    icon_tile(_KIND_ICONS.get(entry.kind, ft.Icons.EXTENSION), letter_hue(entry.package), size=ICON_ROW),
                    ft.Column(
                        [
                            text(entry.package, size=TYPE_BODY, mono=True, no_wrap=True,
                                 overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Row(state, spacing=SPACE_S, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        spacing=SPACE_XS,
                        tight=True,
                        expand=True,
                    ),
                    action,
                ],
                spacing=SPACE_L,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _show_message(
        self, icon: str, title: str, body: str, hue: str = "blue", *, spinner: bool = False, toolbar: bool = False
    ) -> None:
        """Replace the list with a message. The toolbar stays only when the user can act on it."""
        state = empty_state(title, body, icon=icon, hue=hue, spinner=spinner)
        self._body.content = ft.Container(expand=True, padding=SPACE_XL, alignment=ft.Alignment.CENTER, content=state)
        self._count.value = ""
        self._toolbar.visible = toolbar
        self.window.update()

    def _confirm_uninstall(self, entry: AppEntry) -> None:
        if entry.kind == SYSTEM:
            message = t("Removed for this user only. Its data stays on the phone.")
        else:
            message = t("The app and its data are deleted.")
        confirm(
            self.window.page,
            title=t("Uninstall {package}?", package=entry.package),
            message=message,
            action_label=t("Uninstall"),
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
            self.window.notify(t("Uninstalled {package}", package=entry.package), success=True)
            await self.activate()
        else:
            self.window.notify(result.output or t("The uninstall did not finish."), error=True)
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
            self.window.notify(t("Restored {package}", package=entry.package), success=True)
            await self.activate()
        else:
            self.window.notify(result.output or t("The restore did not finish."), error=True)
            self._render()

    def _serial(self) -> str | None:
        device = self.window.session.selected_device
        return device.serial if device and device.is_ready else None


def _not_ready_message(device: Device | None) -> tuple[str, str, str, str]:
    """Icon, title, body and hue for the list area when there is no ready device to read from."""
    if device is None:
        return (
            ft.Icons.PHONE_ANDROID,
            t("No device connected"),
            t("Connect a phone with USB debugging on."),
            "blue",
        )
    if device.mode == FASTBOOT:
        return (
            ft.Icons.FLASH_ON,
            t("The phone is in fastboot mode"),
            t("Reboot to Android to manage apps."),
            "violet",
        )
    if device.state == "unauthorized":
        return (
            ft.Icons.LOCK_OUTLINE,
            t("Allow USB debugging on the phone"),
            t("Accept the prompt on the phone."),
            "amber",
        )
    return (
        ft.Icons.USB_OFF,
        t("The device is {state}", state=device.state),
        t("Reconnect the cable."),
        "danger",
    )
