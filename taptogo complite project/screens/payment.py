from datetime import datetime, timezone

import flet as ft

from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_CARD, RADIUS_PILL, TEXT_MUTED
import db
from ui import snackbar_error, snackbar_ok


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payment(
    page,
    uid,
    ctx: dict,
    on_paid_home,
):
    def sync_from_user():
        try:
            u = db.get_user(uid) or {}
        except Exception:
            u = {}
        return (
            float(ctx.get("fare") or u.get("pending_fare") or 0),
            str(ctx.get("from_stop") or u.get("tap_in_stop") or ""),
            str(ctx.get("to_stop") or u.get("pending_to_stop") or ""),
            str(ctx.get("bus_id") or u.get("current_bus_id") or ""),
        )

    fare, from_stop, to_stop, bus_id = sync_from_user()

    bal_ref = ft.Ref[ft.Text]()

    def refresh_balance():
        try:
            u = db.get_user(uid)
            bal = float((u or {}).get("wallet_balance") or 0)
            bal_ref.current.value = f"₹ {bal:.0f}"
            page.update()
        except Exception as e:
            snackbar_error(page, str(e))

    def write_log(method: str):
        db.create_tap_log(
            str(uid),
            bus_id,
            _iso_now(),
            "tap_out",
            from_stop=from_stop,
            to_stop=to_stop,
            fare_deducted=fare,
            payment_method=method,
        )

    def clear_pending():
        db.update_user(
            uid,
            payment_pending=False,
            pending_fare=0.0,
            pending_to_stop="",
            current_bus_id=None,
        )

    def pay_wallet(_):
        try:
            u = db.get_user(uid)
            bal = float((u or {}).get("wallet_balance") or 0)
            if bal < fare:
                snackbar_error(page, "Insufficient balance.")
                return
            db.update_user(uid, wallet_balance=bal - fare)
            write_log("wallet")
            clear_pending()
            snackbar_ok(page, "Paid from wallet.")
            on_paid_home()
        except Exception as e:
            snackbar_error(page, str(e))

    def open_topup(_):
        amt_field = ft.TextField(
            label="Amount (₹)",
            border_radius=RADIUS_CARD,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        def confirm(__):
            try:
                add = float(amt_field.value or "0")
                if add <= 0:
                    return
                u = db.get_user(uid)
                bal = float((u or {}).get("wallet_balance") or 0)
                db.update_user(uid, wallet_balance=bal + add)
                page.pop_dialog()
                refresh_balance()
                snackbar_ok(page, "Wallet topped up.")
            except Exception:
                snackbar_error(page, "Could not top up.")

        sheet = ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Text("Top up wallet", size=18, weight=ft.FontWeight.W_700),
                        amt_field,
                        ft.FilledButton(
                            "Add",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                bgcolor=BRAND_PRIMARY,
                            ),
                            on_click=confirm,
                        ),
                    ],
                ),
            ),
            shape=ft.RoundedRectangleBorder(radius=24),
        )
        page.show_dialog(sheet)

    def pay_upi(_):
        try:
            uri = f"upi://pay?pa=taptogo@upi&pn=TapToGo&am={fare:.2f}&cu=INR"
            page.launch_url(uri)
        except Exception:
            snackbar_error(page, "Could not open UPI app.")

    def manual_upi_done(_):
        try:
            write_log("upi")
            clear_pending()
            snackbar_ok(page, "Payment recorded.")
            on_paid_home()
        except Exception as e:
            snackbar_error(page, str(e))

    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=24,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=20,
            controls=[
                ft.Text("Pay Your Fare", size=28, weight=ft.FontWeight.W_700, color=BRAND_PRIMARY),
                ft.Text(f"₹ {fare:.0f}", size=44, weight=ft.FontWeight.W_800, color="#0f172a"),
                ft.Text(
                    f"{from_stop}  →  {to_stop}",
                    size=14,
                    color=TEXT_MUTED,
                ),
                ft.Container(height=8),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor="#FFFFFF",
                    padding=20,
                    shadow=ft.BoxShadow(
                        blur_radius=16,
                        color=ft.Colors.with_opacity(0.08, "#000000"),
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Wallet Pay", size=16, weight=ft.FontWeight.W_600),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Balance", color=TEXT_MUTED),
                                    ft.Text(ref=bal_ref, value="₹ 0", weight=ft.FontWeight.W_700),
                                ],
                            ),
                            ft.FilledButton(
                                "Pay from Wallet",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                    bgcolor=BRAND_PRIMARY,
                                    padding=16,
                                ),
                                on_click=pay_wallet,
                            ),
                            ft.OutlinedButton(
                                "Top Up Wallet",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                ),
                                on_click=open_topup,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor="#FFFFFF",
                    padding=20,
                    shadow=ft.BoxShadow(
                        blur_radius=16,
                        color=ft.Colors.with_opacity(0.08, "#000000"),
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("UPI Pay", size=16, weight=ft.FontWeight.W_600),
                            ft.FilledButton(
                                "Pay via UPI",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                    bgcolor=BRAND_PRIMARY,
                                    padding=16,
                                ),
                                on_click=pay_upi,
                            ),
                            ft.Text(
                                "After paying in your UPI app, confirm here.",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                            ft.OutlinedButton(
                                "I have paid",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                ),
                                on_click=manual_upi_done,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ), refresh_balance
