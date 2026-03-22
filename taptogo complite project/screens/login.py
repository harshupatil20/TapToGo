import flet as ft

from constants import ADMIN_ID, ADMIN_PASSWORD
import db
from ui import snackbar_error, snackbar_ok

# Dark theme colors (login-specific, not in constants)
BG_DARK = "#0b0e14"
CARD_BG = "#161b22"
INPUT_BG = "#1c2128"
TEXT_WHITE = "#ffffff"
TEXT_MUTED_DARK = "#8b95a5"
LINK_BLUE = "#5da8ff"
GRADIENT_START = "#4a80f0"
GRADIENT_END = "#8e54f7"
DIVIDER_COLOR = "#2d3640"
BORDER_RADIUS_CARD = 24
BORDER_RADIUS_INPUT = 12


def build_login(page, on_logged_in):
    id_field = ft.TextField(
        label="Email or Phone",
        hint_text="Enter your email or phone number",
        border_radius=BORDER_RADIUS_INPUT,
        filled=True,
        bgcolor=INPUT_BG,
        border_color=DIVIDER_COLOR,
        color=TEXT_WHITE,
        cursor_color=LINK_BLUE,
        label_style=ft.TextStyle(color=TEXT_MUTED_DARK, size=12),
        hint_style=ft.TextStyle(color=TEXT_MUTED_DARK, size=14),
    )
    pw_field = ft.TextField(
        label="Password",
        hint_text="Enter your password",
        password=True,
        can_reveal_password=True,
        border_radius=BORDER_RADIUS_INPUT,
        filled=True,
        bgcolor=INPUT_BG,
        border_color=DIVIDER_COLOR,
        color=TEXT_WHITE,
        cursor_color=LINK_BLUE,
        label_style=ft.TextStyle(color=TEXT_MUTED_DARK, size=12),
        hint_style=ft.TextStyle(color=TEXT_MUTED_DARK, size=14),
    )

    def submit(_):
        cid = (id_field.value or "").strip()
        pw = (pw_field.value or "").strip()
        if not cid or not pw:
            snackbar_error(page, "Enter ID and password.")
            return
        if cid == ADMIN_ID and pw == ADMIN_PASSWORD:
            on_logged_in("admin", {"id": cid})
            return
        cond = db.get_conductor(cid)
        if cond and cond.get("password") == pw:
            bus = db.get_bus(cond["bus_id"]) if cond.get("bus_id") else None
            on_logged_in(
                "conductor",
                {
                    "conductor_id": cid,
                    "bus_id": cond.get("bus_id"),
                    "name": (bus or {}).get("conductor_name", "") if bus else "",
                },
            )
            return
        cam = db.get_camera(cid)
        if cam and cam.get("password") == pw:
            on_logged_in(
                "camera",
                {
                    "camera_id": cid,
                    "bus_id": cam.get("bus_id"),
                },
            )
            return
        user = db.verify_user(cid, pw)
        if user:
            on_logged_in("passenger", {"id": user["id"]})
        else:
            snackbar_error(page, "Invalid email or password.")

    def on_social_placeholder(_):
        snackbar_ok(page, "Coming soon")

    # Logo area with gradient
    logo_box = ft.Container(
        width=80,
        height=80,
        border_radius=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=[GRADIENT_START, GRADIENT_END],
        ),
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.4, GRADIENT_START),
            spread_radius=0,
            offset=ft.Offset(0, 4),
        ),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.DIRECTIONS_BUS, color=TEXT_WHITE, size=28),
                ft.Text("Tap2Go", size=10, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
            ],
        ),
    )

    # Gradient Continue button
    continue_btn = ft.Container(
        height=52,
        border_radius=BORDER_RADIUS_INPUT,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[GRADIENT_START, GRADIENT_END],
        ),
        shadow=ft.BoxShadow(
            blur_radius=16,
            color=ft.Colors.with_opacity(0.35, GRADIENT_END),
            spread_radius=0,
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text("Continue", size=16, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
        on_click=submit,
    )

    # Create account link
    create_account = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Text("New to Tap2Go? ", size=14, color=TEXT_MUTED_DARK),
            ft.GestureDetector(
                content=ft.Text(
                    "Create an account",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=LINK_BLUE,
                ),
                on_tap=lambda _: on_logged_in("register", {}),
            ),
        ],
    )

    # Divider with "or continue with"
    divider_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(expand=True, height=1, bgcolor=DIVIDER_COLOR),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Text("or continue with", size=12, color=TEXT_MUTED_DARK),
            ),
            ft.Container(expand=True, height=1, bgcolor=DIVIDER_COLOR),
        ],
    )

    # Social buttons
    google_btn = ft.Container(
        expand=True,
        height=48,
        border_radius=BORDER_RADIUS_INPUT,
        bgcolor=INPUT_BG,
        border=ft.border.all(1, DIVIDER_COLOR),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.G_MOBILEDATA, color=TEXT_WHITE, size=22),
                ft.Text("Google", size=14, color=TEXT_WHITE),
            ],
        ),
        on_click=on_social_placeholder,
    )
    phone_otp_btn = ft.Container(
        expand=True,
        height=48,
        border_radius=BORDER_RADIUS_INPUT,
        bgcolor=INPUT_BG,
        border=ft.border.all(1, DIVIDER_COLOR),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.SMS_OUTLINED, color=TEXT_WHITE, size=22),
                ft.Text("Phone OTP", size=14, color=TEXT_WHITE),
            ],
        ),
        on_click=on_social_placeholder,
    )

    card = ft.Container(
        padding=28,
        border_radius=BORDER_RADIUS_CARD,
        bgcolor=CARD_BG,
        border=ft.border.all(1, DIVIDER_COLOR),
        content=ft.Column(
            spacing=18,
            controls=[
                id_field,
                pw_field,
                continue_btn,
                create_account,
                divider_row,
                ft.Row(
                    spacing=12,
                    controls=[google_btn, phone_otp_btn],
                ),
            ],
        ),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=24,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
            controls=[
                ft.Container(
                    content=logo_box,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(height=12),
                ft.Text("Tap2Go", size=26, weight=ft.FontWeight.W_700, color=TEXT_WHITE, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    "Travel smarter on every ride",
                    size=14,
                    color=TEXT_MUTED_DARK,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=32),
                ft.Container(
                    alignment=ft.alignment.Alignment(-1, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=4,
                        controls=[
                            ft.Text("Welcome back 👋", size=22, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                            ft.Text("Ready for your next ride?", size=15, color=TEXT_MUTED_DARK),
                        ],
                    ),
                ),
                ft.Container(height=20),
                card,
                ft.Container(height=40),
                ft.Text(
                    "Secure smart travel for your city.",
                    size=12,
                    color=TEXT_MUTED_DARK,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )
