"""Reboot actions. The ADB and fastboot screens share this layout and differ in their commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import Device
from adb_toolkit.core.process import CommandResult
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CARD_PADDING,
    ICON_INLINE,
    RADIUS_CARD,
    SCROLL_PADDING,
    SECTION_GAP,
    SPACE_L,
    SPACE_S,
    TYPE_TITLE,
    palette,
)
from adb_toolkit.ui.views.base import View
from adb_toolkit.ui.widgets import button, icon_tile, screen_frame, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

TARGET_CARD_WIDTH = 264  # three across on a wide window, two on a narrow one


@dataclass(frozen=True)
class RebootTarget:
    # The texts are English keys. They are translated when the screen is built.
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
        icon: str,
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

        cards: list[ft.Control] = []
        for index, item in enumerate(targets):
            reboot = button(
                "outlined",
                t("Reboot"),
                disabled=True,
                on_click=lambda _, entry=item, position=index: self.window.page.run_task(self._reboot, entry, position),
            )
            self._buttons.append(reboot)
            cards.append(_target_card(item, reboot))

        # The cards wrap, and the hint under them says why the buttons are off. The list scrolls.
        self.body = ft.ListView(
            [
                ft.Row(cards, spacing=SPACE_L, run_spacing=SPACE_L, wrap=True),
                ft.Container(content=self._hint),
            ],
            expand=True,
            spacing=SECTION_GAP,
            padding=SCROLL_PADDING,
        )
        self.control = screen_frame(title, self.body, subtitle=subtitle, icon=icon, hue=hue)

    def add_section(self, block: ft.Control) -> None:
        """Add another card below the reboot cards."""
        self.body.controls.append(block)

    async def activate(self) -> None:
        device = self.window.session.selected_device
        ready = device is not None and self._accepts(device)
        for reboot in self._buttons:
            reboot.disabled = not ready or self._busy
        # The hint says why the buttons are off. It stays hidden when they are on.
        self._hint.value = ""
        if device is None:
            self._hint.value = t("Connect a phone to reboot it.")
        elif not ready:
            self._hint.value = self._not_accepted_hint(device)
        self.window.update()

    async def _reboot(self, item: RebootTarget, position: int) -> None:
        device = self.window.session.selected_device
        if device is None or not self._accepts(device):
            self.window.notify(t("The device is not ready for this command."), error=True)
            return
        reboot = self._buttons[position]
        original = reboot.content
        # While the command runs, every reboot button is off and the pressed one shows a spinner.
        reboot.content = _pending_label(t("Rebooting"))
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
            self.window.notify(t(item.done), success=True)
        else:
            self.window.notify(result.output or t("The reboot did not go through."), error=True)


def _target_card(item: RebootTarget, reboot: ft.Control) -> ft.Container:
    """One reboot target: its tile, name and what it does, with the button across the foot of the card."""
    colors = palette()
    return ft.Container(
        width=TARGET_CARD_WIDTH,
        padding=CARD_PADDING,
        border_radius=RADIUS_CARD,
        bgcolor=colors.panel,
        border=ft.Border.all(1, colors.line),
        content=ft.Column(
            [
                icon_tile(item.icon, item.hue),
                ft.Container(height=SPACE_L),
                text(t(item.title), size=TYPE_TITLE, strong=True),
                ft.Container(height=SPACE_S),
                text(t(item.description), color=colors.muted),
                ft.Container(height=SPACE_L),
                reboot,
            ],
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
    )


def _pending_label(label: str) -> ft.Row:
    return ft.Row(
        [
            ft.ProgressRing(width=ICON_INLINE, height=ICON_INLINE, stroke_width=2),
            text(label, strong=True),
        ],
        spacing=SPACE_S,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
