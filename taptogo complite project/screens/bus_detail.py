import flet as ft

from components.stop_chip import stop_chip
from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_CARD, TEXT_MUTED
import db
from ui import snackbar_error


def build_bus_detail(page, bus_id: str, from_stop: str, to_stop: str, on_back):
    header = ft.Ref[ft.Column]()
    stops_row = ft.Ref[ft.Row]()
    sched_row = ft.Ref[ft.Row]()
    people_txt = ft.Ref[ft.Text]()

    def load():
        try:
            b = db.get_bus(bus_id)
        except Exception as e:
            snackbar_error(page, str(e))
            return
        if not b:
            snackbar_error(page, "Bus not found.")
            return
        stops = b.get("stops") or []
        sched = b.get("schedule") or []
        header.current.controls.clear()
        header.current.controls.append(
            ft.Text(
                f"{b.get('bus_no', '')}",
                size=28,
                weight=ft.FontWeight.W_700,
                color=BRAND_PRIMARY,
            )
        )
        header.current.controls.append(
            ft.Text(str(b.get("bus_name", "")), size=16, color="#0f172a")
        )
        header.current.controls.append(
            ft.Text(f"Conductor: {b.get('conductor_name', '—')}", size=14, color=TEXT_MUTED)
        )

        stops_row.current.controls.clear()
        for s in stops:
            hl = s == from_stop or s == to_stop
            stops_row.current.controls.append(stop_chip(str(s), highlighted=hl))

        sched_row.current.controls.clear()
        for t in sched:
            sched_row.current.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor="#EEF2F7",
                    content=ft.Text(str(t), size=12, color=TEXT_MUTED),
                )
            )

        cnt = int(b.get("people_count") or 0)
        people_txt.current.value = f"People on board: {cnt}"
        page.update()

    root = ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=20,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            icon_color=BRAND_PRIMARY,
                            style=ft.ButtonStyle(shape=ft.CircleBorder()),
                            on_click=lambda _: on_back(),
                        ),
                        ft.Text("Bus details", size=18, weight=ft.FontWeight.W_600, color=BRAND_PRIMARY),
                    ]
                ),
                ft.Column(ref=header, spacing=6),
                ft.Text("Route", size=14, color=TEXT_MUTED),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor="#FFFFFF",
                    padding=14,
                    content=ft.Row(
                        ref=stops_row,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=10,
                    ),
                ),
                ft.Text("Schedule", size=14, color=TEXT_MUTED),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor="#FFFFFF",
                    padding=14,
                    content=ft.Row(
                        ref=sched_row,
                        spacing=10,
                        run_spacing=10,
                        wrap=True,
                    ),
                ),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor=ft.Colors.with_opacity(0.12, BRAND_PRIMARY),
                    padding=16,
                    content=ft.Text(
                        ref=people_txt,
                        value="People on board: —",
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=BRAND_PRIMARY,
                    ),
                ),
            ],
        ),
    )
    return root, load
