import datetime

import flet as ft

from components.active_trip_card import build_active_trip_card
from components.bus_card import bus_card
from components.wallet_chip import wallet_chip
from constants import (
    BG_PAGE, BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY, BRAND_SECONDARY,
    ACCENT_TEAL, ACCENT_AMBER, TEXT_MUTED, TEXT_WHITE,
    RADIUS_CARD, RADIUS_PILL, THANE_STOPS, GRAD_START, GRAD_END,
)
from fare_logic import calculate_fare
import db
from ui import snackbar_error


# ── Colour tokens (local override for this screen) ──────────────────────────
_BG       = "#0D1117"
_CARD     = "#161B27"
_CARD_EL  = "#1C2333"
_BORDER   = "rgba(255,255,255,0.06)"
_GRAD_A   = "#3B82F6"
_GRAD_B   = "#7C3AED"


# ── Helper: time-of-day greeting ────────────────────────────────────────────
def _greeting() -> str:
    h = datetime.datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 17:
        return "Good afternoon"
    return "Good evening"


def _route_ok(stops: list, a: str, b: str) -> bool:
    if not stops or a not in stops or b not in stops:
        return False
    return stops.index(a) < stops.index(b)


def _next_dep(schedule: list) -> str:
    if not schedule:
        return "—"
    return str(schedule[0])


# ── AI Seat Availability Predictor ──────────────────────────────────────────
def predict_seat_availability(route_stops: list, current_time=None) -> dict:
    now = current_time or datetime.datetime.now()
    hour = now.hour
    weekday = now.weekday()          # 0=Monday, 6=Sunday
    num_stops = len(route_stops) if route_stops else 10

    is_peak    = weekday < 5 and (8 <= hour <= 10 or 17 <= hour <= 20)
    is_offpeak = hour < 7 or hour > 21 or weekday >= 5

    if is_peak:
        predicted_seats = max(2, 40 - num_stops)
        label = "Crowded"
        color = "#FF4D4D"
    elif is_offpeak:
        predicted_seats = min(50, 30 + num_stops)
        label = "Seats Available"
        color = "#00E5CC"
    else:
        predicted_seats = 18
        label = "Filling Up"
        color = "#F5A623"

    return {"seats": predicted_seats, "label": label, "color": color}


# ── Reusable design primitives ───────────────────────────────────────────────
def _glass_card(content, padding=18) -> ft.Container:
    """Glassmorphism card."""
    return ft.Container(
        border_radius=18,
        bgcolor=_CARD,
        border=ft.border.all(1, "rgba(255,255,255,0.06)"),
        padding=padding,
        content=content,
    )


def _grad_button(label: str, on_click, expand=True) -> ft.Container:
    return ft.Container(
        height=52,
        expand=expand,
        border_radius=RADIUS_PILL,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[_GRAD_A, _GRAD_B],
        ),
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.4, "#6366F1"),
            spread_radius=0,
            offset=ft.Offset(0, 6),
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text(label, size=16, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
        on_click=on_click,
    )


def _styled_dd(label: str, options: list) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        border_radius=18,
        filled=True,
        bgcolor=_CARD_EL,
        border_color="rgba(255,255,255,0.08)",
        color=TEXT_WHITE,
        options=[ft.dropdown.Option(s) for s in options],
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
    )


# ── Main build function ──────────────────────────────────────────────────────
def build_home(page, uid, on_bus_detail, bus_detail_id=None, on_back_from_bus=None, trip=None, from_stop="", to_stop=""):
    last_route   = {"from": from_stop or "", "to": to_stop or ""}
    name_ref     = ft.Ref[ft.Text]()
    wallet_ref   = ft.Ref[ft.Row]()
    results      = ft.Ref[ft.Column]()
    fare_ref     = ft.Ref[ft.Text]()
    crowd_bar    = ft.Ref[ft.Container]()
    seat_num_ref = ft.Ref[ft.Text]()
    seat_lbl_ref = ft.Ref[ft.Container]()
    show_crowd_info = [False]
    crowd_info_switcher_ref = ft.Ref[ft.AnimatedSwitcher]()

    from_dd = _styled_dd("From stop", THANE_STOPS)
    to_dd   = _styled_dd("To stop",   THANE_STOPS)
    from_dd.value = last_route.get("from") or None
    to_dd.value = last_route.get("to") or None

    # ── Live Crowd data (mock — would be from DB in production) ─────────────
    crowd_pct  = 58          # percent
    crowd_lvl  = "Medium"
    crowd_col  = ACCENT_AMBER
    bar_max_w  = 300         # px (approximation — expands via expand)

    # Initial AI prediction using all stops as default
    ai = predict_seat_availability(THANE_STOPS)

    # ── Callbacks ────────────────────────────────────────────────────────────
    def render_wallet(balance: float):
        wallet_ref.current.controls.clear()
        wallet_ref.current.controls.append(wallet_chip(balance))

    def refresh_header():
        try:
            u  = db.get_user(uid)
            nm = (u or {}).get("name") or "Traveller"
            bal = float((u or {}).get("wallet_balance") or 0)
            name_ref.current.value = f"{_greeting()}, {nm}"
            render_wallet(bal)
            page.update()
        except Exception as e:
            snackbar_error(page, str(e))

    def _update_fare():
        a = from_dd.value
        b = to_dd.value
        if a and b and a != b:
            try:
                stops = THANE_STOPS
                buses = db.list_buses()
                for bus in buses:
                    bstops = bus.get("stops") or []
                    if a in bstops and b in bstops:
                        stops = bstops
                        break
                fare = calculate_fare(a, b, stops)
                fare_ref.current.value = f"₹{fare:.0f}"
                # Update AI prediction (only when crowd cards are visible)
                if seat_num_ref.current and seat_lbl_ref.current:
                    ai2 = predict_seat_availability(stops)
                    seat_num_ref.current.value = f"{ai2['seats']} Seats"
                    seat_lbl_ref.current.bgcolor = ft.Colors.with_opacity(0.15, ai2["color"])
                    seat_lbl_ref.current.content.color = ai2["color"]
                    seat_lbl_ref.current.content.value = ai2["label"]
            except Exception:
                fare_ref.current.value = "—"
        else:
            fare_ref.current.value = "—"
        page.update()

    def on_stop_change(e):
        both_selected = bool(from_dd.value) and bool(to_dd.value)
        show_crowd_info[0] = both_selected
        _update_fare()
        if crowd_info_switcher_ref.current:
            crowd_info_switcher_ref.current.content = (
                ft.Column(spacing=16, controls=[card_crowd, card_ai])
                if both_selected
                else ft.Container()
            )
        page.update()
        if both_selected:
            _animate_crowd_bar()

    from_dd.on_change = on_stop_change
    to_dd.on_change = on_stop_change

    selected_bus = None
    if bus_detail_id:
        try:
            selected_bus = db.get_bus(bus_detail_id)
        except Exception:
            pass

    def find_buses():
        a = from_dd.value
        b = to_dd.value
        last_route["from"] = a or ""
        last_route["to"]   = b or ""
        if not a or not b:
            snackbar_error(page, "Select both stops.")
            return
        if a == b:
            snackbar_error(page, "Choose different stops.")
            return
        try:
            buses = db.list_buses()
        except Exception as e:
            snackbar_error(page, str(e))
            return
        results.current.controls.clear()
        for bus in buses:
            bid   = bus.get("id")
            stops = bus.get("stops") or []
            if not _route_ok(stops, a, b):
                continue
            results.current.controls.append(
                bus_card(
                    str(bus.get("bus_no", "")),
                    str(bus.get("bus_name", "")),
                    _next_dep(bus.get("schedule") or []),
                    len(stops),
                    lambda e, bus_id=bid: on_bus_detail(
                        bus_id, last_route["from"], last_route["to"],
                    ),
                )
            )
        if not results.current.controls:
            results.current.controls.append(
                ft.Text("No buses for this route.", color=TEXT_MUTED, size=14)
            )
        page.update()

    # ── HEADER ───────────────────────────────────────────────────────────────
    header = ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Logo + brand
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=38, height=38,
                                border_radius=12,
                                gradient=ft.LinearGradient(
                                    begin=ft.alignment.Alignment(-1, -1),
                                    end=ft.alignment.Alignment(1, 1),
                                    colors=[_GRAD_A, _GRAD_B],
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.DIRECTIONS_BUS, color=TEXT_WHITE, size=20),
                            ),
                            ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("TapToGo", size=18, weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                                    ft.Text("Travel Smarter", size=11, color=TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                    # Wallet pill
                    ft.Row(ref=wallet_ref, spacing=8),
                ],
            ),
            # Greeting
            ft.Text(
                ref=name_ref,
                value=f"{_greeting()}, Traveller",
                size=13,
                color=TEXT_MUTED,
                weight=ft.FontWeight.W_400,
            ),
        ],
    )

    # ── ACTIVE TRIP CARD (Merged Plan Your Trip + Route) ───────────────────
    active_trip_card = build_active_trip_card(
        page,
        from_dd,
        to_dd,
        fare_ref,
        last_route,
        selected_bus,
        trip,
        find_buses,
        on_back_from_bus if on_back_from_bus else (lambda: None),
        lambda: None,
    )

    # ── CARD 3 — Live Crowd Density ──────────────────────────────────────
    crowd_badge = ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.18, crowd_col),
        content=ft.Text(crowd_lvl, size=12, weight=ft.FontWeight.W_700, color=crowd_col),
    )

    progress_track = ft.Container(
        height=6,
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.12, _GRAD_A),
        content=ft.Stack(
            controls=[
                ft.Container(
                    ref=crowd_bar,
                    width=0,
                    height=6,
                    border_radius=999,
                    animate=ft.Animation(800, ft.AnimationCurve.EASE_OUT),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.Alignment(-1, 0),
                        end=ft.alignment.Alignment(1, 0),
                        colors=[_GRAD_A, _GRAD_B],
                    ),
                ),
            ],
        ),
    )

    card_crowd = _glass_card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            spacing=3,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.PEOPLE_ROUNDED, color=_GRAD_A, size=18),
                                        ft.Text("Live Crowd", size=15, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                                    ],
                                ),
                                ft.Text("CURRENT OCCUPANCY", size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                            ],
                        ),
                        crowd_badge,
                    ],
                ),
                ft.Text(f"{crowd_pct}%", size=36, weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                progress_track,
            ],
        )
    )

    # ── CARD 4 — AI Seat Availability ────────────────────────────────────
    seat_label_pill = ft.Container(
        ref=seat_lbl_ref,
        padding=ft.padding.symmetric(horizontal=14, vertical=6),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.15, ai["color"]),
        content=ft.Text(
            ai["label"],
            size=12,
            weight=ft.FontWeight.W_700,
            color=ai["color"],
        ),
    )

    card_ai = _glass_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Text("🪑", size=18),
                        ft.Column(
                            spacing=1, expand=True,
                            controls=[
                                ft.Text("Seat Availability", size=15, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                                ft.Text("AI Prediction", size=11, color=TEXT_MUTED),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("🪑", size=20),
                        ft.Text(
                            ref=seat_num_ref,
                            value=f"{ai['seats']} Seats",
                            size=30,
                            weight=ft.FontWeight.W_800,
                            color=TEXT_WHITE,
                        ),
                    ],
                ),
                seat_label_pill,
                ft.Text(
                    "Based on time & route history",
                    size=11,
                    color=TEXT_MUTED,
                ),
            ],
        )
    )

    # ── Assemble everything ───────────────────────────────────────────────
    def _animate_crowd_bar():
        """Call after first render to animate bar width."""
        try:
            page_w = page.width or 360
            target = (crowd_pct / 100) * (page_w - 72)   # card padding 36*2
            crowd_bar.current.width = target
            page.update()
        except Exception:
            pass

    crowd_info_switcher = ft.AnimatedSwitcher(
        ref=crowd_info_switcher_ref,
        content=ft.Container(),
        duration=400,
        transition=ft.AnimatedSwitcherTransition.FADE,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
    )

    root = ft.Container(
        expand=True,
        bgcolor=_BG,
        padding=ft.padding.symmetric(horizontal=18, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                header,
                active_trip_card,
                crowd_info_switcher,
                ft.Text("RESULTS", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_700),
                ft.Column(ref=results, spacing=14),
                ft.Container(height=16),
            ],
        ),
    )

    def refresh():
        refresh_header()
        _animate_crowd_bar()

    return root, refresh
