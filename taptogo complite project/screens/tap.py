"""
screens/tap.py — Premium NFC Tap screen.
All NFC polling, tap-in/tap-out logic and on_onboard callback are UNCHANGED.
Only the visual layout has been redesigned.
"""
import random
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import flet as ft

from constants import (
    BG_PAGE, BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY,
    TEXT_MUTED, TEXT_WHITE, RADIUS_CARD, RADIUS_PILL,
    GRAD_START, GRAD_END, get_nfc_tmp_paths,
)
from fare_logic import calculate_fare
import db
from ui import snackbar_error


# ─── Local design tokens ────────────────────────────────────────────────────
_BG        = "#0D1117"
_CARD      = "#161B27"
_CARD_R    = "#1A2236"         # scan card background
_INDIGO    = "#6366F1"
_TEAL      = "#00E5CC"
_AMBER     = "#F5A623"
_RED       = "#FF4D4D"


# ─── NFC file helpers (UNCHANGED) ───────────────────────────────────────────
def _read_and_clear_nfc_file() -> str | None:
    for p in get_nfc_tmp_paths():
        try:
            if p.exists():
                text = p.read_text().strip()
                if text:
                    p.write_text("")
                    return text
        except OSError:
            continue
    return None


# ─── Shared UI helpers ───────────────────────────────────────────────────────
def _grad_button(label: str, on_click, expand=True) -> ft.Container:
    return ft.Container(
        height=52, expand=expand,
        border_radius=RADIUS_PILL,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[GRAD_START, GRAD_END],
        ),
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.4, GRAD_END),
            offset=ft.Offset(0, 6),
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text(label, size=16, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
        on_click=on_click,
    )


def _row_info(label: str, value: str, value_color: str = TEXT_WHITE) -> ft.Column:
    return ft.Column(
        spacing=0,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, size=12, color=TEXT_MUTED),
                    ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=value_color),
                ],
            ),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.05, TEXT_WHITE)),
        ],
    )


# ─── Main build function ─────────────────────────────────────────────────────
def build_tap(page, uid, on_onboard):
    status_text  = ft.Ref[ft.Text]()
    status_pill  = ft.Ref[ft.Container]()
    scan_card    = ft.Ref[ft.Container]()   # swapped when tap succeeds
    active       = {"on": True}

    # ── BOTTOM SHEET helper (UNCHANGED logic) ────────────────────────────────
    def finish_scan(bus_id: str, bus: dict):
        stops = bus.get("stops") or []
        tap_in = ft.Dropdown(
            label="Tap-in stop",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
            border_radius=RADIUS_CARD,
            filled=True,
            bgcolor=BG_CARD_ELEVATED,
            border_color="#2A3350",
            color=TEXT_WHITE,
            options=[ft.dropdown.Option(s) for s in stops],
        )
        dest = ft.Dropdown(
            label="Your destination",
            label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
            border_radius=RADIUS_CARD,
            filled=True,
            bgcolor=BG_CARD_ELEVATED,
            border_color="#2A3350",
            color=TEXT_WHITE,
            options=[ft.dropdown.Option(s) for s in stops],
        )

        def confirm(_):
            a = tap_in.value
            b = dest.value
            if not a or not b:
                snackbar_error(page, "Select tap-in and destination.")
                return
            if a not in stops or b not in stops:
                snackbar_error(page, "Invalid stop selection.")
                return
            if stops.index(a) >= stops.index(b):
                snackbar_error(page, "Destination must be after tap-in on this route.")
                return
            try:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                db.update_user(uid, current_bus_id=bus_id, tap_in_stop=a, tap_in_time=ts)
                db.create_tap_log(
                    str(uid), bus_id, ts, "tap_in",
                    from_stop=a, to_stop=b,
                    fare_deducted=0.0, payment_method="n/a",
                )
                est_fare = calculate_fare(a, b, stops)
                page.pop_dialog()
                # ── Swap scan card to success state ────────────────────────
                _show_success_card(bus, a, est_fare)
                on_onboard(bus_id, bus, a, b)
            except Exception as e:
                snackbar_error(page, str(e))

        bs = ft.BottomSheet(
            ft.Container(
                padding=24,
                bgcolor=_CARD,
                border_radius=ft.border_radius.only(top_left=24, top_right=24),
                content=ft.Column(
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text("Bus found 🚌", size=18, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                        ft.Text(
                            f"{bus.get('bus_no','')} · {bus.get('bus_name','')}",
                            size=14, color=TEXT_MUTED,
                        ),
                        ft.Container(height=10),
                        tap_in,
                        dest,
                        ft.Container(height=6),
                        _grad_button("Continue", confirm),
                    ],
                ),
            ),
            shape=ft.RoundedRectangleBorder(radius=24),
        )
        page.show_dialog(bs)

    def _show_success_card(bus: dict, tap_stop: str, est_fare: float):
        """Replace scan card with success state."""
        route_name = f"{bus.get('bus_no','')} · {bus.get('bus_name','')}"
        scan_card.current.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=72, color=_TEAL),
                ft.Text("Tap In Successful!", size=20, weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                ft.Text(f"Bus {bus.get('bus_no','')}  •  {tap_stop}", size=13, color=TEXT_MUTED),
                ft.Container(
                    width=float("inf"),
                    border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.06, TEXT_WHITE),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.07, TEXT_WHITE)),
                    padding=16,
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            _row_info("Route",      route_name),
                            _row_info("Boarded at", tap_stop),
                            _row_info("Status",     "Active", _TEAL),
                            _row_info("Est. Fare",  f"₹{est_fare:.0f}", _TEAL),
                        ],
                    ),
                ),
            ],
        )
        scan_card.current.bgcolor = ft.Colors.with_opacity(0.08, _TEAL)
        scan_card.current.border  = ft.border.all(1, ft.Colors.with_opacity(0.3, _TEAL))
        # Update status pill → success
        status_text.current.value = "Tap In ✓"
        status_pill.current.bgcolor = ft.Colors.with_opacity(0.12, _TEAL)
        status_pill.current.border  = ft.border.all(1, ft.Colors.with_opacity(0.4, _TEAL))
        page.update()

    # ── NFC match logic (UNCHANGED) ─────────────────────────────────────────
    def try_match(sig: str):
        if not sig or not sig.strip():
            return
        nfc_uid = sig.strip()
        try:
            bus = db.get_bus_by_nfc(nfc_uid)
        except Exception as e:
            snackbar_error(page, str(e))
            return
        if not bus:
            snackbar_error(page, "Unknown tag, try again")
            return
        bus_id = bus.get("id")
        status_text.current.value = "Bus found"
        page.update()
        finish_scan(bus_id, bus)

    async def poll_nfc():
        while active["on"]:
            nfc_uid = _read_and_clear_nfc_file()
            if nfc_uid:
                try_match(nfc_uid)
            await asyncio.sleep(1)

    page.run_task(poll_nfc)

    # ===== NFC BETA MODE START =====
    def beta_mode_skip_nfc(_):
        """Bypass NFC: randomly select a bus and open tap-in sheet."""
        try:
            buses = db.list_buses() or []
            if not buses:
                snackbar_error(page, "No buses available. Add buses in Admin.")
                return
            bus = None
            for b in buses:
                if str(b.get("bus_no") or "").upper() == "C-42":
                    bus = b
                    break
            if not bus:
                bus = random.choice(buses)
            bus_id = bus.get("id")
            if bus_id:
                status_text.current.value = "Bus found (Beta)"
                page.update()
                finish_scan(bus_id, bus)
        except Exception as e:
            snackbar_error(page, str(e))

    # ===== NFC BETA MODE END =====

    # ── Animated rings ───────────────────────────────────────────────────────
    outer_ring = ft.Container(
        width=200, height=200,
        border_radius=999,
        border=ft.border.all(2, ft.Colors.with_opacity(0.3, _INDIGO)),
        alignment=ft.alignment.Alignment(0, 0),
        animate=ft.Animation(1200, ft.AnimationCurve.EASE_IN_OUT),
        scale=1.0, opacity=1.0,
    )
    inner_ring = ft.Container(
        width=150, height=150,
        border_radius=999,
        border=ft.border.all(2, ft.Colors.with_opacity(0.5, _INDIGO)),
        alignment=ft.alignment.Alignment(0, 0),
        animate=ft.Animation(1200, ft.AnimationCurve.EASE_IN_OUT),
        scale=1.0, opacity=0.85,
    )
    nfc_core = ft.Container(
        width=100, height=100,
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.18, _INDIGO),
        alignment=ft.alignment.Alignment(0, 0),
        shadow=ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.45, _INDIGO),
            offset=ft.Offset(0, 0),
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            controls=[
                ft.Icon(ft.Icons.NFC_ROUNDED, size=48, color=_INDIGO),
                ft.Text("SCANNING", size=9, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
            ],
        ),
    )

    async def run_pulse():
        while active["on"]:
            outer_ring.scale   = 1.08
            outer_ring.opacity = 0.7
            inner_ring.scale   = 1.05
            page.update()
            await asyncio.sleep(0.6)
            if not active["on"]:
                break
            outer_ring.scale   = 1.0
            outer_ring.opacity = 1.0
            inner_ring.scale   = 1.0
            page.update()
            await asyncio.sleep(0.6)

    page.run_task(run_pulse)

    # ── NFC rings Stack ──────────────────────────────────────────────────────
    rings_stack = ft.Container(
        width=220, height=220,
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Stack(
            alignment=ft.alignment.Alignment(0, 0),
            controls=[
                ft.Container(
                    width=220, height=220,
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.1, _INDIGO),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(
                    width=200, height=200,
                    alignment=ft.alignment.Alignment(0, 0),
                    content=outer_ring,
                ),
                ft.Container(
                    width=150, height=150,
                    alignment=ft.alignment.Alignment(0, 0),
                    content=inner_ring,
                ),
                ft.Container(
                    width=100, height=100,
                    alignment=ft.alignment.Alignment(0, 0),
                    content=nfc_core,
                ),
            ],
        ),
    )

    # ── Main scan card content ────────────────────────────────────────────────
    scan_card_content = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            rings_stack,
            ft.Text(
                ref=status_text,
                value="Tap your phone on the bus tag",
                size=16,
                weight=ft.FontWeight.W_600,
                color=_INDIGO,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Make sure NFC is enabled in settings",
                size=13, color=TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.OutlinedButton(
                "BETA MODE – Skip NFC",
                icon=ft.Icons.DEVICES_OTHER_ROUNDED,
                on_click=beta_mode_skip_nfc,
                style=ft.ButtonStyle(
                    color=_AMBER,
                    side=ft.BorderSide(1, _AMBER),
                ),
            ),
        ],
    )

    # ── Status pill (top-right header) ───────────────────────────────────────
    nfc_status_pill = ft.Container(
        ref=status_pill,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.1, _TEAL),
        border=ft.border.all(1, ft.Colors.with_opacity(0.35, _TEAL)),
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Container(
                    width=7, height=7,
                    border_radius=999,
                    bgcolor=_TEAL,
                    animate=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
                ),
                ft.Text(ref=status_text, value="NFC Ready", size=11,
                        color=_TEAL, weight=ft.FontWeight.W_700),
            ],
        ),
    )

    # ── Recent activity (read-only) ───────────────────────────────────────────
    recent_rows = []
    try:
        logs = db.list_tap_logs_for_user(str(uid)) or []
        if logs:
            d = (logs[0].get("data") or logs[0])
            fare = float(d.get("fare_deducted") or 0)
            ts   = str(d.get("timestamp") or "")[:16].replace("T", "  ")
            route_hint = f"{d.get('from_stop','')} → {d.get('to_stop','')}"
            recent_rows = [
                ft.Container(
                    border_radius=14,
                    bgcolor=_CARD,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.06, TEXT_WHITE)),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("LAST TRIP", size=10, color=TEXT_MUTED,
                                    weight=ft.FontWeight.W_700),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(route_hint, size=13, color=TEXT_WHITE,
                                            weight=ft.FontWeight.W_600, expand=True),
                                    ft.Text(f"₹{fare:.0f}", size=13, color=_TEAL,
                                            weight=ft.FontWeight.W_700),
                                    ft.Text("·", size=13, color=TEXT_MUTED),
                                    ft.Text(ts, size=11, color=TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                )
            ]
    except Exception:
        pass

    # ── Full screen assembly ──────────────────────────────────────────────────
    return ft.Container(
        expand=True,
        bgcolor=_BG,
        padding=ft.padding.symmetric(horizontal=16, vertical=20),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        opacity=1.0,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                # Header row
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("Tap In / Tap Out", size=28,
                                        weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                                ft.Text("Tap your phone on the bus NFC tag",
                                        size=14, color=TEXT_MUTED),
                            ],
                        ),
                        nfc_status_pill,
                    ],
                ),

                # Main scan card
                ft.Container(
                    ref=scan_card,
                    border_radius=24,
                    bgcolor=ft.Colors.with_opacity(0.85, _CARD_R),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.25, _INDIGO)),
                    padding=ft.padding.symmetric(horizontal=24, vertical=32),
                    shadow=ft.BoxShadow(
                        blur_radius=40,
                        color=ft.Colors.with_opacity(0.2, _INDIGO),
                        offset=ft.Offset(0, 8),
                    ),
                    content=scan_card_content,
                ),

                # Recent activity (only if data exists)
                *recent_rows,

                ft.Container(height=12),
            ],
        ),
    )
