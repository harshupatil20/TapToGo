import threading

import flet as ft

try:
    from model_function import webcam
except ImportError:
    webcam = None

from constants import BG_PAGE, BRAND_PRIMARY, RADIUS_PILL, TEXT_MUTED
import db
from ui import snackbar_error, snackbar_ok


def build_camera_portal(page, camera_id: str, bus_id: str, on_offline):
    bus = db.get_bus(bus_id) or {}
    bus_no = str(bus.get("bus_no", ""))
    status = ft.Text("Starting…", size=14, color=TEXT_MUTED)
    active = {"on": True}

    async def startup():
        try:
            db.update_camera(camera_id, stream_active=1)
        except Exception as e:
            snackbar_error(page, str(e))

        if webcam is None:
            status.value = "model_function.webcam is missing. Use the csrnet build that exports webcam(on_result=...)."
            page.update()
            return

        def handle_result(mn, mx):
            async def apply_ui():
                if not active["on"]:
                    return
                status.value = f"{mn}–{mx} people on board"
                try:
                    db.update_bus(
                        bus_id,
                        people_count=int(mx),
                        people_count_min=int(mn),
                        people_count_max=int(mx),
                    )
                except Exception as e:
                    snackbar_error(page, str(e))
                page.update()

            page.run_task(apply_ui)

        def start_webcam():
            try:
                webcam(on_result=handle_result)
            except Exception as ex:
                async def err():
                    status.value = f"Webcam ended or error: {ex}"
                    page.update()

                page.run_task(err)

        threading.Thread(target=start_webcam, daemon=True).start()

    page.run_task(startup)

    def go_offline(_):
        active["on"] = False
        try:
            db.update_camera(camera_id, stream_active=0)
        except Exception as e:
            snackbar_error(page, str(e))
        snackbar_ok(page, "Camera marked offline. Close the OpenCV window (press Q) if it is still open.")
        on_offline()

    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=20,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            controls=[
                ft.Text(
                    f"Camera Active — Bus {bus_no}",
                    size=22,
                    weight=ft.FontWeight.W_700,
                    color=BRAND_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.12, BRAND_PRIMARY),
                    content=status,
                ),
                ft.Text(
                    "Crowd counter runs in a background thread. Each batch updates the bus count. "
                    "Close the cv2 window or press Q there to stop capture.",
                    size=12,
                    color=TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.OutlinedButton(
                    "Go Offline",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL)),
                    on_click=go_offline,
                ),
            ],
        ),
    )
