"""
screens/route_screen.py — Bus Route tab.
Read-only: pulls live data from existing db functions. No logic changes.
Uses a visual stop-strip fallback (no WebView dependency).
"""
import asyncio
import math

import flet as ft

from constants import (
    BG_PAGE, TEXT_MUTED, TEXT_WHITE, RADIUS_CARD,
    GRAD_START, GRAD_END, GOOGLE_MAPS_API_KEY,
)
import db
from utils.eta_simulator import get_stop_etas

# ── Design tokens ────────────────────────────────────────────────────────────
_BG     = "#0D1117"
_CARD   = "#161B27"
_INDIGO = "#6366F1"
_TEAL   = "#00E5CC"
_PURPLE = "#7C3AED"
_BLUE   = "#3B82F6"
_AMBER  = "#F5A623"


def _glass_card(content, padding=18) -> ft.Container:
    return ft.Container(
        border_radius=18,
        bgcolor=_CARD,
        border=ft.border.all(1, "rgba(255,255,255,0.06)"),
        padding=padding,
        content=content,
    )


def _info_chip(label: str) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.12, _INDIGO),
        border=ft.border.all(1, ft.Colors.with_opacity(0.25, _INDIGO)),
        content=ft.Text(label, size=12, color=TEXT_WHITE),
    )


def build_route_screen(page, uid, trip):
    # State
    buses_list: list = []
    selected_bus: dict = {}
    active = {"on": True}

    # Refs
    subtitle_ref     = ft.Ref[ft.Text]()
    map_col_ref      = ft.Ref[ft.Column]()
    stops_col_ref    = ft.Ref[ft.Column]()
    info_row_ref     = ft.Ref[ft.Row]()
    bus_dd_ref       = ft.Ref[ft.Dropdown]()
    stops_expand_ref = ft.Ref[ft.Column]()
    stops_visible    = {"on": False}

    # Live pill dot
    live_dot = ft.Container(
        width=8, height=8, border_radius=999, bgcolor=_TEAL,
        animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1.0,
    )

    async def pulse_live():
        while active["on"]:
            try:
                live_dot.opacity = 0.3
                page.update()
                await asyncio.sleep(0.6)
                if not active["on"]:
                    break
                live_dot.opacity = 1.0
                page.update()
                await asyncio.sleep(0.6)
            except Exception:
                active["on"] = False
                break

    page.run_task(pulse_live)

    # ── Visual route strip ────────────────────────────────────────────────────
    def _build_route_strip(stops: list, current_stop_idx: int, user_stop: str):
        controls = []
        for i, stop in enumerate(stops):
            is_current = (i == current_stop_idx)
            is_user    = (stop == user_stop)

            # Dot color
            if is_current:
                dot_color = _TEAL
                dot_size  = 14
            elif is_user:
                dot_color = _PURPLE
                dot_size  = 12
            else:
                dot_color = ft.Colors.with_opacity(0.4, _BLUE)
                dot_size  = 10

            stop_dot = ft.Container(
                width=dot_size, height=dot_size,
                border_radius=999,
                bgcolor=dot_color,
                shadow=ft.BoxShadow(
                    blur_radius=8 if (is_current or is_user) else 0,
                    color=ft.Colors.with_opacity(0.5, dot_color),
                ) if (is_current or is_user) else None,
            )

            label_extras = []
            if is_current:
                label_extras = [
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=999,
                        bgcolor=ft.Colors.with_opacity(0.15, _TEAL),
                        content=ft.Text("🚌 Bus Here", size=10,
                                        weight=ft.FontWeight.W_700, color=_TEAL),
                    )
                ]
            elif is_user:
                label_extras = [
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=999,
                        bgcolor=ft.Colors.with_opacity(0.15, _PURPLE),
                        content=ft.Text("📍 You", size=10,
                                        weight=ft.FontWeight.W_700, color=_PURPLE),
                    )
                ]

            stop_row = ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        width=16,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Container(
                                width=2, height=12 if i > 0 else 0,
                                bgcolor=ft.Colors.with_opacity(0.3, _BLUE),
                            ),
                            stop_dot,
                            ft.Container(
                                width=2,
                                height=12 if i < len(stops) - 1 else 0,
                                bgcolor=ft.Colors.with_opacity(0.3, _BLUE),
                            ),
                        ],
                    ),
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(stop, size=13,
                                    weight=ft.FontWeight.W_700 if (is_current or is_user) else ft.FontWeight.W_400,
                                    color=TEXT_WHITE if (is_current or is_user) else TEXT_MUTED),
                            *label_extras,
                        ],
                    ),
                ],
            )
            controls.append(stop_row)
        return controls

    # ── Info chips row ────────────────────────────────────────────────────────
    def _build_info_row(bus: dict):
        stops     = bus.get("stops") or []
        pcount    = int(bus.get("people_count") or 36)
        pmax      = int(bus.get("people_count_max") or 50)
        seats     = max(0, pmax - pcount)
        cur_idx   = int(bus.get("current_stop_index") or 0)
        cur_stop  = stops[cur_idx] if cur_idx < len(stops) else "—"
        return [
            _info_chip(f"🧑 {pcount} Passengers"),
            _info_chip(f"💺 {seats} Seats"),
            _info_chip("🕐 On Time"),
            _info_chip(f"📍 {cur_stop[:14]}"),
        ]

    # ===== STOPS UI START — Route timeline (circles + lines) =====
    def _build_all_stops(stops: list, cur_idx: int, user_stop: str = ""):
        etas = get_stop_etas(stops, cur_idx)
        rows = []
        for i, s in enumerate(stops):
            is_cur = i == cur_idx
            is_user = s == user_stop
            eta_str = etas[i][1] if i < len(etas) else "—"
            if is_cur:
                dot_color, dot_size = _TEAL, 16
                glow = ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.5, _TEAL), spread_radius=0)
            elif is_user:
                dot_color, dot_size = _PURPLE, 14
                glow = ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.4, _PURPLE), spread_radius=0)
            elif i < cur_idx:
                dot_color, dot_size = ft.Colors.with_opacity(0.35, TEXT_MUTED), 10
                glow = None
            else:
                dot_color, dot_size = TEXT_WHITE, 12
                glow = None
            dot = ft.Container(
                width=dot_size, height=dot_size, border_radius=999, bgcolor=dot_color,
                shadow=glow,
            )
            line_c = ft.Colors.with_opacity(0.25, _BLUE) if i <= cur_idx else ft.Colors.with_opacity(0.15, TEXT_MUTED)
            txt_c = _TEAL if is_cur else (TEXT_WHITE if (is_user or i >= cur_idx) else TEXT_MUTED)
            stop_row = ft.Row(
                spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        width=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0,
                        controls=[
                            ft.Container(width=2, height=14 if i > 0 else 0, bgcolor=line_c),
                            dot,
                            ft.Container(width=2, height=14 if i < len(stops) - 1 else 0, bgcolor=line_c),
                        ],
                    ),
                    ft.Column(
                        spacing=4, expand=True,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(s, size=13, weight=ft.FontWeight.W_700 if (is_cur or is_user) else ft.FontWeight.W_400, color=txt_c),
                                    *([ft.Container(padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.15, _TEAL),
                                        content=ft.Text("🚌 Now", size=10, weight=ft.FontWeight.W_700, color=_TEAL))] if is_cur else []),
                                    *([ft.Container(padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.15, _PURPLE),
                                        content=ft.Text("📍 You", size=10, weight=ft.FontWeight.W_700, color=_PURPLE))] if is_user else []),
                                    ft.Text(eta_str, size=11, color=TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                ],
            )
            rows.append(stop_row)
        return rows

    # ===== STOPS UI END =====

    # ── Update map + info on bus change ──────────────────────────────────────
    def update_display(bus: dict):
        if not bus:
            return
        stops    = bus.get("stops") or []
        cur_idx  = int(bus.get("current_stop_index") or 0)
        cur_stop = stops[cur_idx] if cur_idx < len(stops) else ""
        user_stop = ""
        if trip:
            user_stop = trip.get("tap_in", "")

        route_name = f"Route {bus.get('bus_no','')} · {stops[0] if stops else '?'} → {stops[-1] if stops else '?'}"
        subtitle_ref.current.value = route_name

        # ===== MAP SECTION START — Fix blank map, OSM fallback =====
        loc = bus.get("current_location") or {}
        lat = float(loc.get("lat", 19.2183))
        lng = float(loc.get("lng", 72.9781))
        if GOOGLE_MAPS_API_KEY:
            map_url = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={lat},{lng}&zoom=14&size=600x400&scale=2&maptype=roadmap"
                f"&style=feature:all|element:labels.text.fill|color:0x8b9ab0"
                f"&style=feature:all|element:geometry|color:0x161b27"
                f"&markers=color:blue%7C{lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
            )
        else:
            z, n = 14, 2 ** 14
            x = int((lng + 180) / 360 * n)
            lat_rad = math.radians(lat)
            y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)
            map_url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        map_image.src = map_url
        # ===== MAP SECTION END =====

        # Update info chips
        info_row_ref.current.controls.clear()
        info_row_ref.current.controls.extend(_build_info_row(bus))

        # Update all-stops list if visible
        if stops_visible["on"]:
            stops_col_ref.current.controls.clear()
            stops_col_ref.current.controls.extend(_build_all_stops(stops, cur_idx, user_stop))

        try:
            page.update()
        except Exception:
            pass

    def on_bus_change(e):
        val = bus_dd_ref.current.value if bus_dd_ref.current else None
        if val:
            for b in buses_list:
                if str(b.get("id")) == val:
                    selected_bus.clear()
                    selected_bus.update(b)
                    update_display(selected_bus)
                    break

    def toggle_stops(_):
        stops_visible["on"] = not stops_visible["on"]
        stops_expand_ref.current.visible = stops_visible["on"]
        if stops_visible["on"] and selected_bus:
            stops   = selected_bus.get("stops") or []
            cur_idx = int(selected_bus.get("current_stop_index") or 0)
            user_stop = (trip or {}).get("tap_in", "")
            stops_col_ref.current.controls.clear()
            stops_col_ref.current.controls.extend(_build_all_stops(stops, cur_idx, user_stop))
        try:
            page.update()
        except Exception:
            pass

    # ── Build dropdown after loading buses ───────────────────────────────────
    bus_dd = ft.Dropdown(
        ref=bus_dd_ref,
        label="Select bus route",
        label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        border_radius=14,
        filled=True,
        bgcolor="#1C2333",
        border_color="rgba(255,255,255,0.08)",
        color=TEXT_WHITE,
        options=[],
        on_select=on_bus_change,
    )

    # Info row (chips)
    info_row = ft.Row(ref=info_row_ref, wrap=True, spacing=8, run_spacing=8, controls=[])

    # Map image — min height 250px, default OSM tile so not blank on load
    _def_lat, _def_lng = 19.2183, 72.9781
    _z, _n = 14, 2 ** 14
    _x = int((_def_lng + 180) / 360 * _n)
    _y = int((1 - math.asinh(math.tan(math.radians(_def_lat))) / math.pi) / 2 * _n)
    _def_src = f"https://tile.openstreetmap.org/{_z}/{_x}/{_y}.png" if not GOOGLE_MAPS_API_KEY else (
        f"https://maps.googleapis.com/maps/api/staticmap?center={_def_lat},{_def_lng}&zoom=14&size=600x250&scale=2&maptype=roadmap"
        f"&markers=color:blue%7C{_def_lat},{_def_lng}&key={GOOGLE_MAPS_API_KEY}"
    )
    map_image = ft.Image(
        src=_def_src,
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
                    ft.Icon(ft.Icons.MAP_ROUNDED, size=48, color=TEXT_MUTED),
                    ft.Text("Map loading...", size=14, color=TEXT_MUTED),
                    ft.Text("Check connection or API key", size=11, color=TEXT_MUTED),
                ],
            ),
        ),
    )

    # All-stops expandable
    stops_inner = ft.Column(ref=stops_col_ref, spacing=0, controls=[])
    stops_expand = ft.Column(
        ref=stops_expand_ref,
        visible=False,
        controls=[
            ft.Container(height=8),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.06, TEXT_WHITE)),
            stops_inner,
        ],
    )

    card_route_selector = _glass_card(
        ft.Column(spacing=12, controls=[
            ft.Row(spacing=8, controls=[
                ft.Icon(ft.Icons.ROUTE_ROUNDED, color=_BLUE, size=18),
                ft.Column(spacing=1, expand=True, controls=[
                    ft.Text("Choose Route", size=15, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                    ft.Text("Select a bus route", size=12, color=TEXT_MUTED),
                ]),
            ]),
            bus_dd,
        ]),
    )

    card_map = _glass_card(
        ft.Column(spacing=0, controls=[
            ft.Text("Live Route Map", size=14, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
            ft.Container(height=8),
            map_image,
        ]),
        padding=16,
    )

    card_info = _glass_card(
        ft.Column(spacing=10, controls=[
            ft.Text("Bus Info", size=13, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
            info_row,
        ]),
    )

    card_all_stops = _glass_card(
        ft.Column(spacing=0, controls=[
            ft.GestureDetector(
                on_tap=toggle_stops,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("All Stops", size=14, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                        ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, color=TEXT_MUTED, size=20),
                    ],
                ),
            ),
            stops_expand,
        ]),
    )

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    def do_refresh():
        try:
            fresh = db.list_buses() or []
            buses_list.clear()
            buses_list.extend(fresh)

            if not bus_dd_ref.current.options:
                bus_dd_ref.current.options = [
                    ft.dropdown.Option(key=str(b.get("id")),
                                       text=f"{b.get('bus_no','?')} | {b.get('bus_name','')}")
                    for b in fresh
                ]
                if fresh:
                    bus_dd_ref.current.value = str(fresh[0].get("id"))
                    selected_bus.clear()
                    selected_bus.update(fresh[0])
                    update_display(selected_bus)
                page.update()
            else:
                # Re-fetch selected bus for live data
                cur_id = bus_dd_ref.current.value
                if cur_id:
                    refreshed = db.get_bus(cur_id) or {}
                    if refreshed:
                        selected_bus.update(refreshed)
                        update_display(selected_bus)
        except Exception:
            pass

    async def _auto_refresh():
        while active["on"]:
            try:
                do_refresh()
            except RuntimeError:
                active["on"] = False
                break
            except Exception:
                pass
            await asyncio.sleep(10)

    page.run_task(_auto_refresh)

    # ── View assembly ─────────────────────────────────────────────────────────
    view = ft.Container(
        expand=True,
        bgcolor=_BG,
        padding=ft.padding.symmetric(horizontal=18, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                # Header
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text("Bus Route", size=26,
                                    weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                            ft.Text(ref=subtitle_ref, value="Select a route below",
                                    size=14, color=TEXT_MUTED),
                        ]),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=999,
                            bgcolor=ft.Colors.with_opacity(0.1, _TEAL),
                            border=ft.border.all(1, ft.Colors.with_opacity(0.35, _TEAL)),
                            content=ft.Row(spacing=6, tight=True, controls=[
                                live_dot,
                                ft.Text("Live", size=11, color=_TEAL,
                                        weight=ft.FontWeight.W_700),
                            ]),
                        ),
                    ],
                ),
                card_route_selector,
                card_map,
                card_info,
                card_all_stops,
                ft.Container(height=16),
            ],
        ),
    )

    def refresh():
        do_refresh()

    return view, refresh
