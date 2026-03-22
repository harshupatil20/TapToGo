import asyncio

import flet as ft

from components.stop_chip import stop_chip
from constants import (
    BG_PAGE, BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY, TEXT_MUTED, TEXT_WHITE,
    RADIUS_PILL, GOOGLE_MAPS_API_KEY, GRAD_START, GRAD_END,
)
from fare_logic import calculate_fare
import db
from ui import snackbar_error


def _static_map_url(lat: float, lng: float, dest_lat: float, dest_lng: float, api_key: str) -> str:
    key = api_key or ""
    return (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}&zoom=14&size=480x280&scale=2&maptype=roadmap"
        f"&markers=color:red%7C{lat},{lng}"
        f"&markers=color:green%7C{dest_lat},{dest_lng}"
        f"&key={key}"
    )


def _grad_button(label: str, on_click) -> ft.Container:
    return ft.Container(
        height=52,
        border_radius=RADIUS_PILL,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[GRAD_START, GRAD_END],
        ),
        shadow=ft.BoxShadow(
            blur_radius=18,
            color=ft.Colors.with_opacity(0.35, GRAD_END),
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text(label, size=16, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
        on_click=on_click,
    )


def build_on_board(
    page,
    uid,
    bus_id: str,
    bus: dict,
    tap_in_stop: str,
    dest_stop: str,
    on_need_payment,
):
    title = ft.Ref[ft.Text]()
    stops_row = ft.Ref[ft.Row]()
    map_img = ft.Ref[ft.Image]()
    active = {"on": True}

    def layout():
        stops = bus.get("stops") or []
        title.current.value = f"{bus.get('bus_no','')} · {bus.get('bus_name','')}"
        stops_row.current.controls.clear()
        for s in stops:
            hl = s == tap_in_stop or s == dest_stop
            stops_row.current.controls.append(stop_chip(str(s), highlighted=hl))

    async def poll():
        while active["on"]:
            try:
                b = db.get_bus(bus_id)
                loc = (b or {}).get("current_location") or {}
                lat = float(loc.get("lat") or 19.2183)
                lng = float(loc.get("lng") or 72.9781)
                dlat = lat + 0.015
                dlng = lng + 0.015
                if map_img.current:
                    map_img.current.src = _static_map_url(lat, lng, dlat, dlng, GOOGLE_MAPS_API_KEY)
                page.update()
            except Exception:
                pass
            await asyncio.sleep(5)

    def tap_out(_):
        try:
            b = db.get_bus(bus_id)
            stops = (b or {}).get("stops") or []
            fare = calculate_fare(tap_in_stop, dest_stop, stops)
            db.update_user(
                uid,
                payment_pending=True,
                pending_fare=float(fare),
                pending_to_stop=dest_stop,
            )
            active["on"] = False
            on_need_payment(
                {
                    "fare": float(fare),
                    "from_stop": tap_in_stop,
                    "to_stop": dest_stop,
                    "bus_id": bus_id,
                }
            )
        except Exception as e:
            snackbar_error(page, str(e))

    root = ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=ft.padding.symmetric(horizontal=18, vertical=20),
        content=ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Text(
                    ref=title,
                    value="Bus",
                    size=22,
                    weight=ft.FontWeight.W_800,
                    color=TEXT_WHITE,
                ),
                ft.Text(f"Conductor: {bus.get('conductor_name','—')}", size=14, color=TEXT_MUTED),
                ft.Container(
                    border_radius=16,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    height=240,
                    bgcolor="#0D1117",
                    content=ft.Image(
                        ref=map_img,
                        src=_static_map_url(19.2183, 72.9781, 19.2333, 72.9931, GOOGLE_MAPS_API_KEY),
                        fit="cover",
                        width=480,
                        height=240,
                    ),
                ),
                ft.Text("Stops on this route", size=13, color=TEXT_MUTED,
                        weight=ft.FontWeight.W_600),
                ft.Container(
                    border_radius=16,
                    bgcolor="#161B27",
                    padding=12,
                    content=ft.Row(
                        ref=stops_row,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=10,
                    ),
                ),
                _grad_button("Tap Out — Exit Bus", tap_out),
            ],
        ),
    )
    layout()
    page.run_task(poll)
    return root, lambda: active.update(on=False)
