"""
Cinematic splash animation screen shown after passenger login.
Sequence (2.5 seconds total):
  Stage 1 (0.0s–0.5s)  — "Tap" fades in from left
  Stage 2 (0.5s–1.0s)  — "2Go" fades in from right → "Tap2Go" formed
  Stage 3 (1.0s–2.0s)  — Bus slides left→right, road line extends, subtitle fades
  Stage 4 (2.0s–2.5s)  — whole screen fades out then calls on_done()
"""
import asyncio

import flet as ft

_BG = "#0D1117"
_GRAD_START = "#5B6FFF"
_GRAD_END = "#A259FF"
_WHITE = "#FFFFFF"
_MUTED = "#8B9AB0"


async def build_login_animation(page: ft.Page, on_done) -> None:
    # ── Shared animated state refs ──────────────────────────────────────────
    tap_opacity = ft.Ref[ft.AnimatedSwitcher]()
    go_opacity = ft.Ref[ft.AnimatedSwitcher]()

    # Text elements for "Tap" and "2Go"
    tap_text = ft.Container(
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        opacity=0,
        offset=ft.Offset(-0.3, 0),
        content=ft.Text(
            "Tap",
            size=52,
            weight=ft.FontWeight.W_800,
            color=_WHITE,
        ),
    )

    go_text = ft.Container(
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        opacity=0,
        offset=ft.Offset(0.3, 0),
        content=ft.Text(
            "2Go",
            size=52,
            weight=ft.FontWeight.W_800,
            color=_GRAD_START,
        ),
    )

    logo_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
        controls=[tap_text, go_text],
    )

    # Road line — animates width 0 → full
    road_width = ft.Ref[ft.Container]()
    road_line = ft.Container(
        height=3,
        width=0,
        animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        border_radius=999,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[_GRAD_START, _GRAD_END],
        ),
        ref=road_width,
    )

    # Subtitle
    subtitle = ft.Container(
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        opacity=0,
        offset=ft.Offset(0, 0.3),
        content=ft.Text(
            "Travel Smarter",
            size=16,
            color=_MUTED,
            weight=ft.FontWeight.W_500,
            text_align=ft.TextAlign.CENTER,
        ),
    )

    # Bus — sits in a Stack, slides left→right
    bus_container = ft.Container(
        width=44,
        height=44,
        left=-60,
        animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Text("🚌", size=34),
    )

    # We need page width to know the target x for the bus
    page_w = page.width or 400

    # The road+bus stack sits below the logo
    # Stack needs a fixed height so the bus can be absolutely positioned
    transit_layer = ft.Container(
        width=float("inf"),
        height=52,
        content=ft.Stack(
            controls=[
                ft.Container(
                    top=38,
                    left=0,
                    right=0,
                    content=road_line,
                ),
                bus_container,
            ],
        ),
    )

    # Full-screen wrapper (fades out at the end)
    screen = ft.Container(
        expand=True,
        bgcolor=_BG,
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1.0,
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                logo_row,
                ft.Container(height=4),
                transit_layer,
                ft.Container(height=6),
                subtitle,
            ],
        ),
    )

    # Mount the splash
    page.controls.clear()
    page.add(ft.SafeArea(screen, expand=True))
    page.update()

    # ── Stage 1: 0.0s → 0.5s  — "Tap" fades in ────────────────────────────
    await asyncio.sleep(0.05)
    tap_text.opacity = 1.0
    tap_text.offset = ft.Offset(0, 0)
    page.update()

    # ── Stage 2: 0.5s → 1.0s  — "2Go" fades in ───────────────────────────
    await asyncio.sleep(0.5)
    go_text.opacity = 1.0
    go_text.offset = ft.Offset(0, 0)
    page.update()

    # ── Stage 3: 1.0s → 2.0s  — bus drives, road extends, subtitle appears
    await asyncio.sleep(0.5)
    page_w = page.width or 400
    bus_container.left = float(page_w) + 60
    road_line.width = float(page_w)
    page.update()

    await asyncio.sleep(0.6)
    subtitle.opacity = 1.0
    subtitle.offset = ft.Offset(0, 0)
    page.update()

    # ── Stage 4: 2.0s → 2.5s  — fade out whole screen ────────────────────
    await asyncio.sleep(0.9)
    screen.opacity = 0.0
    page.update()

    await asyncio.sleep(0.5)

    # Hand control back to the caller
    on_done()
