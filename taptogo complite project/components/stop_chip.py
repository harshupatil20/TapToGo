import flet as ft

from constants import BRAND_PRIMARY, RADIUS_CARD, TEXT_MUTED, BG_CARD_ELEVATED, TEXT_WHITE


def stop_chip(
    label: str,
    *,
    highlighted: bool = False,
    compact: bool = False,
) -> ft.Control:
    bg = ft.Colors.with_opacity(0.25, BRAND_PRIMARY) if highlighted else BG_CARD_ELEVATED
    fg = BRAND_PRIMARY if highlighted else TEXT_MUTED
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=RADIUS_CARD if not compact else 999,
        bgcolor=bg,
        content=ft.Text(
            label,
            size=13 if not compact else 12,
            color=fg,
            weight=ft.FontWeight.W_600 if highlighted else ft.FontWeight.W_400,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
    )
