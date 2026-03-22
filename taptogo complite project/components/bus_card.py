import flet as ft

from constants import BG_CARD, BRAND_PRIMARY, RADIUS_CARD, TEXT_MUTED, TEXT_WHITE, ACCENT_TEAL, GRAD_START, GRAD_END


def bus_card(
    bus_no: str,
    bus_name: str,
    next_dep: str,
    stop_count: int,
    on_tap,
) -> ft.Control:
    return ft.Container(
        on_click=on_tap,
        border_radius=RADIUS_CARD,
        bgcolor=BG_CARD,
        padding=20,
        animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            bus_no,
                            size=20,
                            weight=ft.FontWeight.W_700,
                            color=TEXT_WHITE,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=999,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.Alignment(-1, 0),
                                end=ft.alignment.Alignment(1, 0),
                                colors=[GRAD_START, GRAD_END],
                            ),
                            content=ft.Text(
                                f"{stop_count} stops",
                                size=12,
                                color=TEXT_WHITE,
                                weight=ft.FontWeight.W_600,
                            ),
                        ),
                    ],
                ),
                ft.Text(bus_name, size=15, color=TEXT_WHITE, weight=ft.FontWeight.W_500),
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=14, color=ACCENT_TEAL),
                        ft.Text(
                            f"Next: {next_dep}",
                            size=13,
                            color=TEXT_MUTED,
                        ),
                    ],
                ),
            ],
        ),
    )
