"""
screens/admin/fare_config.py — Admin Fare System.
Base fare + distance-based increment. Max fare cap.
"""
import flet as ft

from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_CARD, RADIUS_PILL, TEXT_MUTED, TEXT_WHITE
from fare_logic import get_fare_config, set_fare_config
from ui import snackbar_ok, snackbar_error

# ===== ADMIN FARE SYSTEM START =====

_BG = "#0D1117"
_CARD = "#161B27"
_GRAD_A = "#3B82F6"
_GRAD_B = "#7C3AED"


def build_fare_config(page, on_back):
    cfg = get_fare_config()
    base_tf = ft.TextField(
        label="Base Fare (₹)",
        value=str(cfg["base_fare"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#1C2333",
        border_color="rgba(255,255,255,0.08)",
        color=TEXT_WHITE,
    )
    inc_tf = ft.TextField(
        label="Per-Stop Increment (₹)",
        value=str(cfg["per_stop_increment"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#1C2333",
        border_color="rgba(255,255,255,0.08)",
        color=TEXT_WHITE,
    )
    max_tf = ft.TextField(
        label="Maximum Fare (₹)",
        value=str(cfg["max_fare"]),
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#1C2333",
        border_color="rgba(255,255,255,0.08)",
        color=TEXT_WHITE,
    )

    def save(_):
        try:
            base = int(base_tf.value or "10")
            inc = int(inc_tf.value or "2")
            mx = int(max_tf.value or "45")
            set_fare_config(base_fare=base, per_stop_increment=inc, max_fare=mx)
            snackbar_ok(page, "Fare settings saved.")
        except ValueError:
            snackbar_error(page, "Enter valid numbers.")

    return ft.Container(
        expand=True,
        bgcolor=_BG,
        padding=24,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            on_click=lambda _: on_back(),
                            icon_color=TEXT_WHITE,
                        ),
                        ft.Text("Fare Settings", size=22, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                        ft.Container(width=48),
                    ],
                ),
                ft.Text(
                    "Base fare + (stops × increment). Capped at max.",
                    size=13,
                    color=TEXT_MUTED,
                ),
                ft.Container(
                    padding=20,
                    border_radius=18,
                    bgcolor=_CARD,
                    border=ft.border.all(1, "rgba(255,255,255,0.06)"),
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            base_tf,
                            inc_tf,
                            max_tf,
                            ft.Container(
                                height=48,
                                border_radius=RADIUS_PILL,
                                gradient=ft.LinearGradient(
                                    begin=ft.alignment.Alignment(-1, 0),
                                    end=ft.alignment.Alignment(1, 0),
                                    colors=[_GRAD_A, _GRAD_B],
                                ),
                                content=ft.Text("Save", size=16, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                                alignment=ft.alignment.Alignment(0, 0),
                                on_click=save,
                            ),
                        ],
                    ),
                ),
                ft.Text("Example: 5 stops → ₹10 + 5×₹2 = ₹20", size=12, color=TEXT_MUTED),
            ],
        ),
    )


# ===== ADMIN FARE SYSTEM END =====
