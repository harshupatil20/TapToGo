import flet as ft

from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_PILL, TEXT_MUTED


def build_admin_home(page, on_add_bus, on_view_buses, on_fare_config, on_logout):
    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=24,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Text("Admin Portal", size=28, weight=ft.FontWeight.W_700, color=BRAND_PRIMARY),
                ft.Text("Manage buses and devices", size=14, color=TEXT_MUTED),
                ft.FilledButton(
                    "Add New Bus",
                    width=260,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                        bgcolor=BRAND_PRIMARY,
                        padding=18,
                    ),
                    on_click=lambda _: on_add_bus(),
                ),
                ft.FilledButton(
                    "View All Buses",
                    width=260,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                        bgcolor=BRAND_PRIMARY,
                        padding=18,
                    ),
                    on_click=lambda _: on_view_buses(),
                ),
                ft.FilledButton(
                    "Fare Settings",
                    width=260,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                        bgcolor=BRAND_PRIMARY,
                        padding=18,
                    ),
                    on_click=lambda _: on_fare_config(),
                ),
                ft.TextButton("Logout", on_click=lambda _: on_logout(), style=ft.ButtonStyle(color=BRAND_PRIMARY)),
            ],
        ),
    )
