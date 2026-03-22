import flet as ft

from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_CARD, RADIUS_PILL, TEXT_MUTED
import db
from ui import snackbar_error, snackbar_ok


def build_register(page, on_done):
    name_f = ft.TextField(
        label="Name",
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#FFFFFF",
    )
    email_f = ft.TextField(
        label="Email",
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#FFFFFF",
    )
    phone_f = ft.TextField(
        label="Phone",
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#FFFFFF",
    )
    pw_f = ft.TextField(
        label="Password",
        password=True,
        border_radius=RADIUS_CARD,
        filled=True,
        bgcolor="#FFFFFF",
    )

    def save(_):
        email = (email_f.value or "").strip()
        pw = pw_f.value or ""
        if not email or not pw:
            snackbar_error(page, "Enter email and password.")
            return
        try:
            uid = db.create_user(
                name_f.value or "",
                email,
                phone_f.value or "",
                pw,
            )
            snackbar_ok(page, "Account created.")
            on_done()
        except Exception as e:
            if "UNIQUE" in str(e) or "unique" in str(e).lower():
                snackbar_error(page, "Email already registered.")
            else:
                snackbar_error(page, str(e))

    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=24,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            icon_color=BRAND_PRIMARY,
                            style=ft.ButtonStyle(shape=ft.CircleBorder()),
                            on_click=lambda _: on_done(),
                        ),
                        ft.Text("Create account", size=22, weight=ft.FontWeight.W_700, color=BRAND_PRIMARY),
                    ]
                ),
                ft.Text("We only need a few details.", size=14, color=TEXT_MUTED),
                name_f,
                email_f,
                phone_f,
                pw_f,
                ft.Container(
                    alignment=ft.alignment.Alignment.CENTER,
                    padding=ft.padding.only(top=12),
                    content=ft.FilledButton(
                        "Register",
                        width=280,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                            bgcolor=BRAND_PRIMARY,
                            padding=16,
                        ),
                        on_click=save,
                    ),
                ),
            ],
        ),
    )
