import flet as ft

from constants import BG_PAGE, BG_CARD, BRAND_PRIMARY, RADIUS_CARD, TEXT_MUTED, TEXT_WHITE
import db
from ui import snackbar_error


def build_view_buses(page, on_back, on_edit):
    col = ft.Column(spacing=14)

    def load():
        col.controls.clear()
        try:
            rows = db.list_buses()
        except Exception as e:
            snackbar_error(page, str(e))
            page.update()
            return
        if not rows:
            col.controls.append(ft.Text("No buses yet.", color=TEXT_MUTED))
            page.update()
            return
        for b in rows:
            bid = b.get("id")
            col.controls.append(
                ft.Container(
                    on_click=lambda e, bus_id=bid: on_edit(bus_id),
                    border_radius=RADIUS_CARD,
                    bgcolor=BG_CARD,
                    padding=18,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(str(b.get("bus_no", "")), size=18, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                            ft.Text(
                                f"{len(b.get('stops') or [])} stops · {b.get('conductor_name','')}",
                                size=13,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                )
            )
        page.update()

    load()

    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=20,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(ft.Icons.ARROW_BACK_ROUNDED, on_click=lambda _: on_back(),
                                      icon_color=TEXT_WHITE),
                        ft.Text("All buses", size=22, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                    ]
                ),
                ft.Column(col, expand=True, scroll=ft.ScrollMode.AUTO),
            ],
        ),
    ), load
