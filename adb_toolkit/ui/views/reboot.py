"""Reboot actions. The ADB and fastboot screens share this layout and differ in their commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.process import CommandResult
from adb_toolkit.ui.theme import ICON_INLINE, SCROLL_PADDING, SECTION_GAP, SPACE_S, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import button, hairline, screen_frame, spec_row, spec_section, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


@dataclass(frozen=True)
class RebootTarget:
    target: str | None  # None means "reboot to Android"
    title: str
    description: str
    done: str  # shown once the command has been sent
    icon: str
    hue: str  # colour of the icon, one of the palette's hue names


class RebootView(View):
    def __init__(
        self,
        window: Window,
        *,
        title: str,
        subtitle: str,
        hue: str,
        targets: tuple[RebootTarget, ...],
        accepts: Callable[[Device], bool],
        not_accepted_hint: Callable[[Device], str],
        send: Callable[[str, str | None], CommandResult],
    ) -> None:
        super().__init__(window)
        self._targets = targets
        self._accepts = accepts
        self._not_accepted_hint = not_accepted_hint
        self._send = send
        self._busy = False
        self._hint = text("", color=palette().muted)
        self._buttons: list[ft.Control] = []

        rows: list[ft.Control] = []
        for index, item in enumerate(targets):
            if index:
                rows.append(hairline())
            reboot = button(
                "outlined",
                "Reboot",
                disabled=True,
                on_click=lambda _, entry=item, position=index: self.window.page.run_task(self._reboot, entry, position),
            )
            self._buttons.append(reboot)
            rows.append(spec_row(item.title, item.description, reboot, icon=item.icon, hue=item.hue))
        rows.append(ft.Container(padding=ft.Padding.only(top=SPACE_S), content=self._hint))

        # The sections sit in a list that scrolls; the screen header stays where it is.
        self.body = ft.ListView(
            [spec_section("Reboot", rows, description="Send the phone to another mode.")],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(title, self.body, subtitle=subtitle, hue=hue)

    def add_section(self, block: ft.Control) -> None:
        """Add another spec section below the reboot section, with a hairline between them."""
        self.body.controls.append(ft.Container(content=hairline()))
        self.body.controls.append(block)

    async def activate(self) -> None:
        device = self.window.session.selected_device
        ready = device is not None and self._accepts(device)
        for reboot in self._buttons:
            reboot.disabled = not ready or self._busy
        # The hint says why the buttons are off. It stays hidden when they are on.
        self._hint.value = ""
        if device is None:
            self._hint.value = "Connect a phone to reboot it."
        elif not ready:
            self._hint.value = self._not_accepted_hint(device)
        self.window.update()

    async def _reboot(self, item: RebootTarget, position: int) -> None:
        device = self.window.session.selected_device
        if device is None or not self._accepts(device):
            self.window.notify("The device is not ready for this command.", error=True)
            return
        reboot = self._buttons[position]
        original = reboot.content
        # While the command runs, every reboot button is off and the pressed one shows a spinner.
        reboot.content = _pending_label("Rebooting")
        self._busy = True
        await self.activate()
        reboot.update()
        try:
            result = await self.window.run_blocking(self._send, device.serial, item.target)
        finally:
            reboot.content = original
            self._busy = False
            await self.activate()
            reboot.update()
        if result.ok:
            self.window.notify(item.done, success=True)
        else:
            self.window.notify(result.output or "The reboot did not go through.", error=True)


def _pending_label(label: str) -> ft.Row:
    return ft.Row(
        [
            ft.ProgressRing(width=ICON_INLINE, height=ICON_INLINE, stroke_width=2),
            text(label),
        ],
        spacing=SPACE_S,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
