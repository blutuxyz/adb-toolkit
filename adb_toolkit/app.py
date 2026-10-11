"""Start the app: create the Flet page and hand it to the window."""

import flet as ft

from adb_toolkit.config import ASSETS_DIR
from adb_toolkit.core.session import Session
from adb_toolkit.ui.window import Window


async def _main(page: ft.Page) -> None:
    window = Window(page, Session())
    await window.start()


def run(*, web: bool = False, port: int = 8550) -> None:
    """Open the desktop window. With web=True, serve the same UI to a browser at localhost:port."""
    if web:
        ft.run(_main, assets_dir=str(ASSETS_DIR), view=ft.AppView.WEB_BROWSER, port=port)
    else:
        ft.run(_main, assets_dir=str(ASSETS_DIR))
