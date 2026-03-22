"""
components/active_trip_card.py — Unified Active Trip Card.
Merges Plan Your Trip + Route/Bus details into one component.
"""
from __future__ import annotations

import math

import flet as ft

from constants import THANE_STOPS, GOOGLE_MAPS_API_KEY
from fare_logic import calculate_fare
from utils.eta_simulator import get_stop_etas, get_eta_for_stop
import db
from ui import snackbar_error

# ===== ACTIVE TRIP CARD START =====

_CARD = "#161B27"
_GRAD_A = "#3B82F6"
_GRAD_B = "#7C3AED"
_TEAL = "#00E5CC"
_PURPLE = "#7C3AED"
_BLUE = "#3B82F6"
_AMBER = "#F5A623"
_MUTED = "#8B9AB0"
_WHITE = "#FFFFFF"


def _osm_tile_url(lat: float, lng: float, z: int = 14) -> str:
    """Single OSM tile as fallback when Google API key missing."""
    n = 2 ** z
    x = int((lng + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)
    return f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def _google_static_map_url(lat: float, lng: float, w: int = 600, h: int = 250) -> str:
    url = (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}&zoom=14&size={w}x{h}&scale=2&maptype=roadmap"
        f"&style=feature:all|element:labels.text.fill|color:0x8b9ab0"
        f"&style=feature:all|element:geometry|color:0x161b27"
        f"&markers=color:blue%7C{lat},{lng}"
    )
    if GOOGLE_MAPS_API_KEY:
        url += f"&key={GOOGLE_MAPS_API_KEY}"
    return url


# ===== MAP SECTION START =====
def _build_map(lat: float, lng: float) -> ft.Container:
    """Map: min height 250px. Tries WebView+Leaflet if flet_webview installed, else static image."""
    try:
        import base64
        import flet_webview as fwv
        from utils.map_html import get_map_html
        html = get_map_html(lat, lng, height="250px")
        data_url = "data:text/html;base64," + base64.b64encode(html.encode()).decode()
        wv = fwv.WebView(url=data_url, expand=False)
        return ft.Container(
            height=250,
            width=float("inf"),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=12,
            content=wv,
        )
    except Exception:
        pass
    if GOOGLE_MAPS_API_KEY:
        url = _google_static_map_url(lat, lng)
    else:
        url = _osm_tile_url(lat, lng)
    return ft.Container(
        height=250,
        width=float("inf"),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border_radius=12,
        content=ft.Image(
            src=url,
            width=float("inf"),
            height=250,
            fit="cover",
            border_radius=12,
            error_content=ft.Container(
                height=250,
                alignment=ft.alignment.Alignment(0, 0),
                bgcolor=ft.Colors.with_opacity(0.1, _BLUE),
                border_radius=12,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.MAP_ROUNDED, size=48, color=_MUTED),
                        ft.Text("Map loading...", size=14, color=_MUTED),
                        ft.Text("Check connection or API key", size=11, color=_MUTED),
                    ],
                ),
            ),
        ),
    )


# ===== MAP SECTION END =====


# ===== STOPS UI START — Route Timeline =====
def _build_route_timeline(stops: list, cur_idx: int, user_stop: str, from_s: str, to_s: str) -> ft.Column:
    """Vertical route flow with circles, lines, highlights."""
    etas = get_stop_etas(stops, cur_idx)
    controls = []
    for i, stop in enumerate(stops):
        is_current = i == cur_idx
        is_user = stop == user_stop
        is_highlight = is_user or stop == from_s or stop == to_s
        eta_str = etas[i][1] if i < len(etas) else "—"

        if is_current:
            dot_color, dot_size = _TEAL, 16
            glow = ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.5, _TEAL), spread_radius=0)
        elif is_highlight:
            dot_color, dot_size = _PURPLE, 14
            glow = ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.4, _PURPLE), spread_radius=0)
        elif i < cur_idx:
            dot_color, dot_size = ft.Colors.with_opacity(0.35, _MUTED), 10
            glow = None
        else:
            dot_color, dot_size = _WHITE, 12
            glow = None

        dot = ft.Container(
            width=dot_size, height=dot_size, border_radius=999, bgcolor=dot_color,
            shadow=glow, border=ft.border.all(2, dot_color if is_current or is_highlight else "transparent"),
        )

        label_extras = []
        if is_current:
            label_extras.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.15, _TEAL),
                    content=ft.Text("🚌 Now", size=10, weight=ft.FontWeight.W_700, color=_TEAL),
                )
            )
        if is_user:
            label_extras.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.15, _PURPLE),
                    content=ft.Text("📍 You", size=10, weight=ft.FontWeight.W_700, color=_PURPLE),
                )
            )

        line_color = ft.Colors.with_opacity(0.25, _BLUE) if i <= cur_idx else ft.Colors.with_opacity(0.15, _MUTED)
        text_color = _WHITE if (is_current or is_highlight or i >= cur_idx) else _MUTED

        stop_row = ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    width=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0,
                    controls=[
                        ft.Container(width=2, height=14 if i > 0 else 0, bgcolor=line_color),
                        dot,
                        ft.Container(width=2, height=14 if i < len(stops) - 1 else 0, bgcolor=line_color),
                    ],
                ),
                ft.Column(
                    spacing=4, expand=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Text(stop, size=13, weight=ft.FontWeight.W_700 if (is_current or is_highlight) else ft.FontWeight.W_400, color=text_color),
                                *label_extras,
                                ft.Text(eta_str, size=11, color=_MUTED),
                            ],
                        ),
                    ],
                ),
            ],
        )
        controls.append(stop_row)
    return ft.Column(spacing=0, controls=controls)


# ===== STOPS UI END =====


def _glass_card(content, padding=18) -> ft.Container:
    return ft.Container(
        border_radius=18,
        bgcolor=_CARD,
        border=ft.border.all(1, "rgba(255,255,255,0.06)"),
        padding=padding,
        content=content,
    )


def build_active_trip_card(
    page,
    from_dd: ft.Dropdown,
    to_dd: ft.Dropdown,
    fare_ref: ft.Ref[ft.Text],
    last_route: dict,
    bus: dict | None,
    trip: dict | None,
    on_find_buses,
    on_back_from_bus,
    on_tap_out,
) -> ft.Container:
    """
    Unified Active Trip Card. Renders planning or expanded mode based on bus/trip.
    """
    is_onboard = bool(trip)
    show_expanded = bus is not None
    from_s = last_route.get("from", "") or (from_dd.value if from_dd else "")
    to_s = last_route.get("to", "") or (to_dd.value if to_dd else "")
    user_stop = (trip or {}).get("tap_in", "")

    top_section = ft.Column(
        spacing=12,
        controls=[
            from_dd,
            to_dd,
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Estimated Fare", size=12, color=_MUTED),
                    ft.Text(ref=fare_ref, value="—", size=18, weight=ft.FontWeight.W_800, color=_WHITE),
                ],
            ),
        ],
    )

    bus_info = ft.Column(spacing=8, controls=[])
    map_ctrl = ft.Container()
    stops_ctrl = ft.Column(spacing=0, controls=[], visible=False)

    if show_expanded and bus:
        stops = bus.get("stops") or []
        cur_idx = int(bus.get("current_stop_index") or 0)
        loc = bus.get("current_location") or {}
        lat = float(loc.get("lat", 19.2183))
        lng = float(loc.get("lng", 72.9781))
        pcount = int(bus.get("people_count") or 36)
        pmax = int(bus.get("people_count_max") or 50)
        seats = max(0, pmax - pcount)
        eta_dest = get_eta_for_stop(stops, cur_idx, to_s) if to_s else "—"

        bus_info.controls = [
            ft.Row(
                wrap=True, spacing=8, run_spacing=8,
                controls=[
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.12, _BLUE),
                                content=ft.Text(f"Route {bus.get('bus_no','?')}", size=12, color=_WHITE)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.12, _TEAL),
                                content=ft.Text(f"🧑 {pcount} on board", size=12, color=_TEAL)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.12, _AMBER),
                                content=ft.Text(f"💺 {seats} seats", size=12, color=_AMBER)),
                    ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=6), border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.12, _PURPLE),
                                content=ft.Text(f"ETA {eta_dest}", size=12, color=_PURPLE)),
                ],
            ),
            ft.Text(f"Conductor: {bus.get('conductor_name','—')} • {'Medium' if pcount > 30 else 'Low'} crowd", size=11, color=_MUTED),
        ]

        map_ctrl = _build_map(lat, lng)
        stops_ctrl.controls = [_build_route_timeline(stops, cur_idx, user_stop, from_s, to_s)]
        stops_ctrl.visible = True

    def on_primary_click(_):
        if show_expanded:
            if is_onboard:
                on_tap_out()
            else:
                on_back_from_bus()
        else:
            on_find_buses()

    primary_btn = ft.Container(
        height=52,
        expand=True,
        border_radius=999,
        gradient=ft.LinearGradient(begin=ft.alignment.Alignment(-1, 0), end=ft.alignment.Alignment(1, 0), colors=[_GRAD_A, _GRAD_B]),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.4, _GRAD_B), offset=ft.Offset(0, 6)),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text(
            "Tap Out — Exit Bus" if (show_expanded and is_onboard) else ("Find Another Bus" if show_expanded else "Find Buses"),
            size=16, weight=ft.FontWeight.W_700, color=_WHITE,
        ),
        on_click=on_primary_click,
    )

    card_controls = [
        ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.ROUTE_ROUNDED, color=_GRAD_B, size=20),
            ft.Text("Active Trip", size=18, weight=ft.FontWeight.W_800, color=_WHITE),
        ]),
        top_section,
    ]
    if show_expanded:
        card_controls.append(bus_info)
        card_controls.append(map_ctrl)
        card_controls.append(stops_ctrl)
    card_controls.append(primary_btn)

    return _glass_card(ft.Column(spacing=18, controls=card_controls))


# ===== ACTIVE TRIP CARD END =====
