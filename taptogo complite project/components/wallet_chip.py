import flet as ft

from constants import GRAD_START, GRAD_END, TEXT_WHITE, RADIUS_PILL


def wallet_chip(balance: float) -> ft.Control:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border_radius=RADIUS_PILL,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[GRAD_START, GRAD_END],
        ),
        content=ft.Row(
            spacing=4,
            tight=True,
            controls=[
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=14, color=TEXT_WHITE),
                ft.Text(
                    f"₹{balance:.0f}",
                    size=13,
                    weight=ft.FontWeight.W_700,
                    color=TEXT_WHITE,
                ),
            ],
        ),
    )
