"""UI helpers (SnackBars, etc.)."""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft


def snackbar_error(page, msg: str, on_ok: Optional[Callable] = None) -> None:
    def close(_):
        sn.open = False
        page.update()
        if on_ok:
            on_ok()

    sn = ft.SnackBar(
        content=ft.Text(msg, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        behavior=ft.SnackBarBehavior.FLOATING,
        shape=ft.RoundedRectangleBorder(radius=16),
        action="OK",
        on_action=close,
    )
    page.overlay.append(sn)
    sn.open = True
    page.update()


def snackbar_ok(page, msg: str) -> None:
    sn = ft.SnackBar(
        content=ft.Text(msg, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_700,
        behavior=ft.SnackBarBehavior.FLOATING,
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.overlay.append(sn)
    sn.open = True
    page.update()
