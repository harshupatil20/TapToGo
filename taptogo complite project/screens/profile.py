import flet as ft

from constants import (
    BG_PAGE, BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY, BRAND_SECONDARY,
    ACCENT_TEAL, TEXT_MUTED, TEXT_WHITE, RADIUS_CARD, RADIUS_PILL,
    GRAD_START, GRAD_END,
)
import db
from ui import snackbar_error, snackbar_ok


def _initials(name: str) -> str:
    parts = (name or "").strip().split()
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _grad_button(label: str, on_click, expand=True) -> ft.Container:
    return ft.Container(
        height=48,
        expand=expand,
        border_radius=RADIUS_PILL,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[GRAD_START, GRAD_END],
        ),
        shadow=ft.BoxShadow(
            blur_radius=14,
            color=ft.Colors.with_opacity(0.3, GRAD_END),
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text(label, size=14, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
        on_click=on_click,
    )


def _dark_card(content, padding=20) -> ft.Container:
    return ft.Container(
        border_radius=RADIUS_CARD,
        bgcolor=BG_CARD,
        padding=padding,
        content=content,
    )


def build_profile(page, uid, on_logout):
    name_f = ft.TextField(
        label="Name",
        label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor=BG_CARD_ELEVATED,
        border_color="#2A3350",
        color=TEXT_WHITE,
        cursor_color=BRAND_PRIMARY,
    )
    email_t = ft.Text(size=14, color=TEXT_MUTED)
    phone_f = ft.TextField(
        label="Phone",
        label_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor=BG_CARD_ELEVATED,
        border_color="#2A3350",
        color=TEXT_WHITE,
        cursor_color=BRAND_PRIMARY,
    )
    avatar_lbl = ft.Ref[ft.Text]()
    bal_lbl = ft.Ref[ft.Text]()
    trips = ft.Ref[ft.Column]()

    def load():
        try:
            u = db.get_user(uid) or {}
            name_f.value = str(u.get("name") or "")
            email_t.value = str(u.get("email") or "")
            phone_f.value = str(u.get("phone") or "")
            avatar_lbl.current.value = _initials(name_f.value)
            bal_lbl.current.value = f"₹{float(u.get('wallet_balance') or 0):.0f}"
        except Exception as e:
            snackbar_error(page, str(e))

        try:
            rows = db.list_tap_logs_for_user(str(uid))
        except Exception:
            rows = []
        trips.current.controls.clear()
        for r in rows[:20]:
            d = r.get("data") or r
            fare = float(d.get("fare_deducted") or 0)
            status_badge_color = "#00B87A" if fare > 0 else BRAND_PRIMARY
            bus_id = d.get("bus_id") or ""
            bus_no = bus_id
            try:
                bus = db.get_bus(bus_id) if bus_id else None
                bus_no = (bus or {}).get("bus_no") or bus_id
            except Exception:
                pass
            ts = str(d.get("timestamp") or "")
            if "T" in ts:
                ts = ts.replace("T", " ")[:16]
            trips.current.controls.append(
                _dark_card(
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.15, BRAND_PRIMARY),
                                        content=ft.Text(f"Route {bus_no}", size=11,
                                                        weight=ft.FontWeight.W_600, color=BRAND_PRIMARY),
                                    ),
                                    ft.Text(f"₹{fare:.0f}", size=16, weight=ft.FontWeight.W_700, color=ACCENT_TEAL),
                                ],
                            ),
                            ft.Text(f"{d.get('from_stop', '')} → {d.get('to_stop', '')}",
                                    size=14, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(ts or "—", size=11, color=TEXT_MUTED),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.15, status_badge_color),
                                        content=ft.Text(
                                            "Completed" if fare > 0 else "Active",
                                            size=11, weight=ft.FontWeight.W_600,
                                            color=status_badge_color,
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    padding=16,
                )
            )
        if not trips.current.controls:
            trips.current.controls.append(
                ft.Container(
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=30,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY_ROUNDED, size=40, color=TEXT_MUTED),
                            ft.Text("No journeys yet", size=14, color=TEXT_MUTED),
                        ],
                    ),
                )
            )
        page.update()

    def save_profile(_):
        try:
            db.update_user(
                uid,
                name=name_f.value or "",
                phone=phone_f.value or "",
            )
            avatar_lbl.current.value = _initials(name_f.value or "")
            snackbar_ok(page, "Profile saved.")
            page.update()
        except Exception as e:
            snackbar_error(page, str(e))

    def topup(amount: float):
        try:
            u = db.get_user(uid) or {}
            bal = float(u.get("wallet_balance") or 0)
            db.update_user(uid, wallet_balance=bal + amount)
            bal_lbl.current.value = f"₹{bal + amount:.0f}"
            snackbar_ok(page, "Wallet updated.")
            page.update()
        except Exception as e:
            snackbar_error(page, str(e))

    def open_topup_sheet(amt: float):
        def confirm(_):
            page.pop_dialog()
            topup(amt)

        bs = ft.BottomSheet(
            ft.Container(
                padding=24,
                bgcolor=BG_CARD,
                border_radius=ft.border_radius.only(top_left=24, top_right=24),
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Text("Confirm top-up", size=18, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                        ft.Text(f"Add ₹{amt:.0f} to wallet (mock).", color=TEXT_MUTED),
                        ft.Container(height=8),
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    "Cancel",
                                    on_click=lambda _: page.pop_dialog(),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                        color=TEXT_MUTED,
                                        side=ft.BorderSide(1, "#2A3350"),
                                    ),
                                ),
                                _grad_button("Confirm", confirm, expand=True),
                            ],
                            spacing=12,
                        ),
                    ],
                ),
            ),
            shape=ft.RoundedRectangleBorder(radius=24),
        )
        page.show_dialog(bs)

    chips = ft.Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                border_radius=999,
                bgcolor=ft.Colors.with_opacity(0.12, BRAND_PRIMARY),
                border=ft.border.all(1, ft.Colors.with_opacity(0.3, BRAND_PRIMARY)),
                content=ft.Text(f"₹{a}", color=BRAND_PRIMARY, size=13, weight=ft.FontWeight.W_600),
                on_click=lambda e, x=a: open_topup_sheet(x),
            )
            for a in [10, 20, 50, 100, 200, 500]
        ],
    )

    root = ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=ft.padding.symmetric(horizontal=18, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                # Page title
                ft.Text("Profile", size=26, weight=ft.FontWeight.W_800, color=TEXT_WHITE),

                # App logo
                ft.Container(
                    alignment=ft.alignment.Alignment(0, 0),
                    content=ft.Container(
                        width=56, height=56,
                        border_radius=16,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.Alignment(-1, -1),
                            end=ft.alignment.Alignment(1, 1),
                            colors=[GRAD_START, GRAD_END],
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.DIRECTIONS_BUS, color=TEXT_WHITE, size=26),
                    ),
                ),

                # Wallet Balance card
                _dark_card(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("WALLET BALANCE", size=11, color=TEXT_MUTED,
                                            weight=ft.FontWeight.W_600),
                                    ft.Text(ref=bal_lbl, value="₹0", size=32,
                                            weight=ft.FontWeight.W_800, color=TEXT_WHITE),
                                ],
                            ),
                            _grad_button("Recharge Wallet", lambda _: open_topup_sheet(100), expand=False),
                        ],
                    )
                ),

                # Cashback card
                _dark_card(
                    ft.Row(
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=40, height=40,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(0.15, "#F5A623"),
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.SAVINGS_ROUNDED, color="#F5A623", size=22),
                            ),
                            ft.Column(
                                spacing=4, expand=True,
                                controls=[
                                    ft.Text("Cashback Rewards", size=15,
                                            weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                                    ft.Text("Get 5% cashback when you pay using the Tap2Go wallet.",
                                            size=12, color=TEXT_MUTED),
                                ],
                            ),
                        ],
                    )
                ),

                # Payments card
                _dark_card(
                    ft.Row(
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=40, height=40,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(0.15, BRAND_PRIMARY),
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
                                                color=BRAND_PRIMARY, size=22),
                            ),
                            ft.Column(
                                spacing=4, expand=True,
                                controls=[
                                    ft.Text("Tap2Go Payments", size=15,
                                            weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                                    ft.Text("Secure in-app payment for every ride.",
                                            size=12, color=TEXT_MUTED),
                                ],
                            ),
                        ],
                    )
                ),

                # User info card
                _dark_card(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.TextField(
                                        ref=None,
                                        label="Name",
                                        label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
                                        border_radius=8,
                                        filled=True,
                                        bgcolor=BG_CARD_ELEVATED,
                                        border_color="#2A3350",
                                        color=TEXT_WHITE,
                                        cursor_color=BRAND_PRIMARY,
                                        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
                                    ),
                                    email_t,
                                    ft.Text("Role: commuter", size=12, color=TEXT_MUTED),
                                    ft.Row(spacing=4, controls=[
                                        ft.Text("Wallet Balance:", size=14,
                                                weight=ft.FontWeight.W_700, color="#00E5CC"),
                                        ft.Text(ref=ft.Ref[ft.Text](), value="₹0",
                                                size=14, weight=ft.FontWeight.W_700, color="#00E5CC"),
                                    ]),
                                ],
                            ),
                            ft.Container(
                                width=64, height=64,
                                border_radius=999,
                                border=ft.border.all(2, BRAND_PRIMARY),
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Text(
                                    ref=avatar_lbl,
                                    value="U",
                                    size=22,
                                    weight=ft.FontWeight.W_700,
                                    color=BRAND_PRIMARY,
                                ),
                            ),
                        ],
                    )
                ),

                # Edit name/phone
                _dark_card(
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Edit Profile", size=14, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                            name_f,
                            phone_f,
                            _grad_button("Save Profile", save_profile),
                        ],
                    )
                ),

                # Recharge chips
                _dark_card(
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Quick Recharge", size=14, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                            chips,
                        ],
                    )
                ),

                # Travel History heading
                ft.Text("Travel History", size=16, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                ft.Column(ref=trips, spacing=12),

                # Logout
                ft.Container(
                    alignment=ft.alignment.Alignment(0, 0),
                    content=ft.TextButton(
                        "Logout",
                        style=ft.ButtonStyle(color=TEXT_MUTED),
                        on_click=lambda _: on_logout(),
                    ),
                ),
            ],
        ),
    )
    return root, load
