"""Fastboot Tools screen: commands for a phone in bootloader (fastboot) mode."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from adb_toolkit.core.devices import FASTBOOT
from adb_toolkit.ui.dialogs import dialog_frame
from adb_toolkit.ui.i18n import t
from adb_toolkit.ui.theme import (
    CONTROL_HEIGHT,
    FONT_MONO,
    RADIUS_CONTROL,
    SPACE_M,
    TYPE_CAPTION,
    palette,
)
from adb_toolkit.ui.views.reboot import RebootTarget, RebootView
from adb_toolkit.ui.widgets import ONE_LINE, PillGroup, ProgressLine, button, card, text

if TYPE_CHECKING:
    from adb_toolkit.ui.window import Window

_TARGETS = (
    RebootTarget(
        None,
        "Reboot system",
        "Restart into Android.",
        "Rebooting the phone.",
        ft.Icons.RESTART_ALT,
        "green",
    ),
    RebootTarget(
        "bootloader",
        "Reboot to bootloader",
        "Stay in fastboot mode.",
        "Rebooting to the bootloader.",
        ft.Icons.FLASH_ON,
        "violet",
    ),
    RebootTarget(
        "recovery",
        "Reboot to recovery",
        "Not every phone supports this.",
        "Rebooting to recovery.",
        ft.Icons.BUILD_CIRCLE_OUTLINED,
        "amber",
    ),
)


class FastbootToolsView(RebootView):
    def __init__(self, window: Window) -> None:
        super().__init__(
            window,
            title=t("Fastboot Tools"),
            subtitle=t("Commands for a phone in bootloader mode."),
            icon=ft.Icons.FLASH_ON_OUTLINED,
            hue="violet",
            targets=_TARGETS,
            accepts=lambda device: device.mode == FASTBOOT,
            not_accepted_hint=lambda device: t("Reboot to the bootloader from ADB Tools first."),
            send=lambda serial, target: window.session.fastboot.reboot(serial, target),
        )
        self.flash = FlashCard(window)
        self.add_section(self.flash.control)

    async def activate(self) -> None:
        await super().activate()
        self.flash.refresh()


class FlashCard:
    """Writes an image to one partition. The partition's name has to be typed again before it runs."""

    def __init__(self, window: Window) -> None:
        self.window = window
        colors = palette()
        self._image: str | None = None
        self._partition = ft.TextField(
            hint_text="boot_a",
            expand=True,
            height=CONTROL_HEIGHT,
            border_radius=RADIUS_CONTROL,
            border_color=colors.control_border,
            focused_border_color=colors.accent,
            cursor_color=colors.accent,
            text_style=ft.TextStyle(font_family=FONT_MONO),
        )
        self._image_name = text("", size=TYPE_CAPTION, mono=True, color=colors.muted, **ONE_LINE)
        self._names = ft.Container()
        self._progress = ProgressLine()
        self._hint = text("", color=colors.muted)
        self._choose = button("outlined", t("Choose image"), icon=ft.Icons.FOLDER_OPEN,
                              on_click=lambda _: self.window.page.run_task(self._pick))
        self._list = button("outlined", t("List partitions"), icon=ft.Icons.LIST,
                            on_click=lambda _: self.window.page.run_task(self._list_partitions))
        self._flash = button("danger", t("Flash"), icon=ft.Icons.FLASH_ON,
                             on_click=lambda _: self._confirm())
        self.control = card(
            t("Flash a partition"),
            [
                ft.Row(
                    [self._partition],
                    spacing=SPACE_M,
                ),
                self._names,
                ft.Row(
                    [self._choose, ft.Container(expand=True, content=self._image_name)],
                    spacing=SPACE_M,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row([self._list, self._flash], spacing=SPACE_M),
                text(t("Flashing needs an unlocked bootloader. A wrong image can stop the phone from starting."),
                     color=colors.signal),
                self._progress.control,
                self._hint,
            ],
            description=t("Writes an image to one partition. Use only an image made for this exact phone."),
            icon=ft.Icons.FLASH_ON,
            hue="violet",
        )

    def refresh(self) -> None:
        device = self.window.session.selected_device
        ready = device is not None and device.mode == FASTBOOT
        busy = self.window.busy
        self._flash.disabled = not ready or busy or self._image is None
        self._list.disabled = not ready or busy
        self._choose.disabled = busy
        self._image_name.value = Path(self._image).name if self._image else t("No file chosen")
        self._hint.value = "" if ready else t("Reboot to the bootloader from ADB Tools first.")
        self.window.update()

    async def _pick(self) -> None:
        chosen = await self.window.pick_files(title=t("Choose an image"), extensions=["img"])
        if chosen:
            self._image = chosen[0]
        self.refresh()

    async def _list_partitions(self) -> None:
        device = self.window.session.selected_device
        if device is None:
            return
        names = await self.window.run_job(self.window.session.fastboot.partitions, device.serial)
        if not names:
            self.window.notify(t("No partitions were listed."), error=True)
            return
        self._names.content = PillGroup(
            tuple((name, name) for name in names), self._partition.value or "", self._pick_partition,
        ).control
        self.window.update()

    def _pick_partition(self, name: str) -> None:
        self._partition.value = name
        self.window.update()

    def _confirm(self) -> None:
        partition = (self._partition.value or "").strip()
        image = self._image
        if not partition or image is None:
            self.window.notify(t("Choose a partition and an image first."), error=True)
            return
        page = self.window.page
        colors = palette()
        field = ft.TextField(
            hint_text=partition,
            autofocus=True,
            height=CONTROL_HEIGHT,
            border_radius=RADIUS_CONTROL,
            border_color=colors.control_border,
            focused_border_color=colors.danger,
            cursor_color=colors.danger,
            text_style=ft.TextStyle(font_family=FONT_MONO),
        )
        confirm = button("danger", t("Flash"), disabled=True, on_click=lambda _: start())

        def typed(event: ft.ControlEvent) -> None:
            value = event.data if isinstance(event.data, str) else event.control.value
            confirm.disabled = (value or "").strip() != partition
            confirm.update()

        def start() -> None:
            page.pop_dialog()
            page.run_task(self._flash, partition, image)

        field.on_change = typed
        page.show_dialog(
            dialog_frame(
                icon=ft.Icons.WARNING_AMBER_OUTLINED,
                hue="danger",
                title=t("Flash {partition}?", partition=partition),
                body=[
                    text(
                        t("This writes {image} to the {partition} partition. The app cannot undo it.",
                          image=Path(image).name, partition=partition),
                        color=colors.muted,
                    ),
                    text(t("Type {partition} to confirm.", partition=partition), color=colors.muted),
                    field,
                ],
                actions=[
                    button("text", t("Cancel"), on_click=lambda _: page.pop_dialog()),
                    confirm,
                ],
            )
        )

    async def _flash(self, partition: str, image: str) -> None:
        device = self.window.session.selected_device
        if device is None or device.mode != FASTBOOT:
            self.window.notify(t("The phone is not in fastboot mode."), error=True)
            return
        self._progress.start(t("Flashing {partition}", partition=partition))
        self.refresh()
        try:
            result = await self.window.run_job(
                self.window.session.fastboot.flash, device.serial, partition, image,
                on_line=self._progress.feed, on_tick=self._progress.tick,
            )
        finally:
            self._progress.hide()
            self.refresh()
        if result.ok:
            self.window.notify(t("Flashed {partition}.", partition=partition), success=True)
        else:
            self.window.notify(result.output or t("The flash did not finish."), error=True)
