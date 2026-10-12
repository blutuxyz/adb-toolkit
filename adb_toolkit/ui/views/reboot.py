"""Reboot actions. The ADB and fastboot screens share this layout and differ in their commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.process import CommandResult
from adb_toolkit.ui.theme import SCROLL_PADDING, SECTION_GAP, palette
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import action_row, hairline, text, title_block

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window


@dataclass(frozen=True)
class RebootTarget:
    target: str | None  # None means "reboot to Android"
    title: str
    description: str
    done: str  # shown once the command has been sent
    icon: str
    hue: str  # colour of the icon tile, one of the palette's hue names


class RebootView(View):
    def __init__(
        self,
        window: Window,
        *,
        title: str,
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
        self._hint = text("", size=13, color=palette().muted)
        self._buttons: list[ft.FilledTonalButton] = []

        rows: list[ft.Control] = []
        for index, item in enumerate(targets):
            if index:
                rows.append(hairline())
            button = ft.FilledTonalButton(
                content=text("Reboot"),
                disabled=True,
                on_click=lambda _, entry=item: self.window.page.run_task(self._reboot, entry),
            )
            self._buttons.append(button)
            rows.append(action_row(item.title, item.description, button, icon=item.icon, hue=item.hue))

        self.control = ft.ListView(
            [
                title_block(title),
                ft.Container(height=SECTION_GAP),
                *rows,
                ft.Container(height=16),
                self._hint,
            ],
            expand=True,
            spacing=0,
            padding=SCROLL_PADDING,
        )

    async def activate(self) -> None:
        device = self.window.session.selected_device
        ready = device is not None and self._accepts(device)
        for button in self._buttons:
            button.disabled = not ready
        # The hint says why the buttons are off. It stays hidden when they are on.
        self._hint.value = ""
        if device is None:
            self._hint.value = "Connect a phone to reboot it."
        elif not ready:
            self._hint.value = self._not_accepted_hint(device)
        self.window.update()

    async def _reboot(self, item: RebootTarget) -> None:
        device = self.window.session.selected_device
        if device is None or not self._accepts(device):
            self.window.notify("The device is not ready for this command.", error=True)
            return
        result = await self.window.run_blocking(self._send, device.serial, item.target)
        if result.ok:
            self.window.notify(item.done, success=True)
        else:
            self.window.notify(result.output or "The reboot did not go through.", error=True)
