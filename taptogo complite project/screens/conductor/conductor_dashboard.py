import asyncio
from datetime import datetime, timezone

import flet as ft

try:
    from model_function import image, video
except ImportError:
    image = video = None

from constants import (
    BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY,
    RADIUS_CARD, RADIUS_PILL, TEXT_MUTED, TEXT_WHITE,
)
import db
from ui import snackbar_error, snackbar_ok


def _today_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _coerce_image_count(result) -> int:
    if isinstance(result, dict):
        return int(result.get("count") or 0)
    return int(result)


def _coerce_video_range(result):
    if isinstance(result, dict):
        if result.get("ok") is False or result.get("error"):
            return None, None
        return result.get("min"), result.get("max")
    if isinstance(result, tuple) and len(result) == 2:
        mn, mx = result[0], result[1]
        if mn is None and mx is None:
            return None, None
        return mn, mx
    return None, None


def build_conductor_dashboard(page, bus_id: str, conductor_name: str):
    bus = db.get_bus(bus_id) or {}
    bus_no = str(bus.get("bus_no", ""))
    camera_id = str(bus.get("camera_id", ""))

    pred = ft.Text("Prediction: —", size=14, color=TEXT_WHITE)
    cam_status = ft.Text("Camera: checking…", size=14, color=TEXT_WHITE)
    live_count = ft.Text("Live count: —", size=14, color=TEXT_WHITE)
    logs_col = ft.Column(spacing=10)
    boarded = ft.Text("Boarded (today): —", size=14, color=TEXT_MUTED)
    _input_style = {
        "border_radius": RADIUS_CARD,
        "filled": True,
        "bgcolor": BG_CARD_ELEVATED,
        "border_color": "rgba(255,255,255,0.12)",
        "color": TEXT_WHITE,
        "cursor_color": BRAND_PRIMARY,
        "label_style": ft.TextStyle(color=TEXT_MUTED, size=12),
    }
    lat_f = ft.TextField(label="Latitude", value="19.2183", **_input_style)
    lng_f = ft.TextField(label="Longitude", value="72.9781", **_input_style)

    last = {"image_count": None, "video_min": None, "video_max": None}

    def apply_picked_path(path: str):
        try:
            if image is None or video is None:
                snackbar_error(page, "Crowd model not available. Install torch, torchvision, opencv-python.")
                return
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                count = _coerce_image_count(image(path))
                last["image_count"] = count
                last["video_min"] = None
                last["video_max"] = None
                pred.value = f"{count} people detected"
            else:
                mn, mx = _coerce_video_range(video(path))
                last["image_count"] = None
                if mn is not None:
                    last["video_min"] = mn
                    last["video_max"] = mx
                    pred.value = f"Between {mn} and {mx} people detected"
                else:
                    last["video_min"] = None
                    last["video_max"] = None
                    pred.value = "Could not process video"
            page.update()
        except Exception as ex:
            snackbar_error(page, f"Model error: {ex}")

    async def pick_file_async(_):
        files = await ft.FilePicker().pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png", "jpg", "jpeg", "webp", "mp4", "mov"],
        )
        if not files:
            return
        path = files[0].path
        if path:
            apply_picked_path(path)

    async def poll_camera():
        while True:
            try:
                cam = db.get_camera(camera_id) if camera_id else None
                active = bool((cam or {}).get("stream_active"))
                cam_status.value = "Camera: Online" if active else "Camera: Offline"
                b = db.get_bus(bus_id) or {}
                mn = b.get("people_count_min")
                mx = b.get("people_count_max")
                pc = b.get("people_count")
                if mn is not None and mx is not None:
                    live_count.value = f"{mn}–{mx} people currently on board"
                elif pc is not None:
                    live_count.value = f"{int(pc)} people currently on board"
                else:
                    live_count.value = "Live count: —"
                page.update()
            except Exception:
                pass
            await asyncio.sleep(5)

    def refresh_logs():
        logs_col.controls.clear()
        try:
            rows = db.list_tap_logs_for_bus(bus_id)
        except Exception as e:
            snackbar_error(page, str(e))
            page.update()
            return
        today = _today_prefix()
        ins = 0
        outs = 0
        for row in rows:
            d = row.get("data") or row
            ts = str(d.get("timestamp") or "")
            if not ts.startswith(today):
                continue
            if d.get("action") == "tap_in":
                ins += 1
            if d.get("action") == "tap_out":
                outs += 1
            logs_col.controls.append(
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor=BG_CARD,
                    padding=12,
                    border=ft.border.all(1, "rgba(255,255,255,0.08)"),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(f"{d.get('user_id','')}", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                            ft.Text(
                                f"{d.get('action','')} · {d.get('timestamp','')}",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                )
            )
        boarded.value = f"Boarded (today): {ins} tap-ins / {outs} tap-outs"
        page.update()

    def pick_file(e):
        page.run_task(pick_file_async, e)

    def push_count(_):
        try:
            if last["image_count"] is not None:
                n = int(last["image_count"])
                db.update_bus(
                    bus_id,
                    people_count=n,
                    people_count_min=n,
                    people_count_max=n,
                )
            elif last["video_min"] is not None and last["video_max"] is not None:
                mn = int(last["video_min"])
                mx = int(last["video_max"])
                db.update_bus(
                    bus_id,
                    people_count=mx,
                    people_count_min=mn,
                    people_count_max=mx,
                )
            else:
                snackbar_error(page, "Run a photo or video prediction first.")
                return
            snackbar_ok(page, "Count updated.")
        except Exception:
            snackbar_error(page, "Could not update count.")

    def sync_live(_):
        try:
            b = db.get_bus(bus_id) or {}
            mx = int(b.get("people_count") or 0)
            mn = b.get("people_count_min")
            if mn is None:
                mn = mx
            db.update_bus(
                bus_id,
                people_count=mx,
                people_count_min=int(mn),
                people_count_max=mx,
            )
            snackbar_ok(page, "Synced live count.")
        except Exception as e:
            snackbar_error(page, str(e))

    def update_gps(_):
        try:
            lat = float(lat_f.value or "0")
            lng = float(lng_f.value or "0")
            db.update_bus(bus_id, current_location={"lat": lat, "lng": lng})
            snackbar_ok(page, "Location updated.")
        except Exception as e:
            snackbar_error(page, str(e))

    page.run_task(poll_camera)
    refresh_logs()

    return ft.Container(
        expand=True,
        bgcolor="#0B1020",
        padding=20,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text(f"Bus {bus_no}", size=24, weight=ft.FontWeight.W_700, color=TEXT_WHITE),
                ft.Text(f"Conductor: {conductor_name}", size=14, color=TEXT_MUTED),
                ft.Text("People count", size=16, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor=BG_CARD,
                    padding=16,
                    border=ft.border.all(1, "rgba(255,255,255,0.08)"),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Upload photo / video", size=14, color=TEXT_MUTED),
                            pred,
                            ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        "Choose file",
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                            bgcolor=BRAND_PRIMARY,
                                        ),
                                        on_click=pick_file,
                                    ),
                                    ft.OutlinedButton(
                                        "Update Bus Count",
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                            color=BRAND_PRIMARY,
                                            side=ft.BorderSide(1, BRAND_PRIMARY),
                                        ),
                                        on_click=push_count,
                                    ),
                                ]
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor=BG_CARD,
                    padding=16,
                    border=ft.border.all(1, "rgba(255,255,255,0.08)"),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Live camera feed", size=14, color=TEXT_MUTED),
                            cam_status,
                            live_count,
                            ft.OutlinedButton(
                                "Sync live count",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                                    color=BRAND_PRIMARY,
                                    side=ft.BorderSide(1, BRAND_PRIMARY),
                                ),
                                on_click=sync_live,
                            ),
                        ],
                    ),
                ),
                ft.Text("NFC tap log (today)", size=16, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                boarded,
                logs_col,
                ft.Text("Bus location", size=16, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                lat_f,
                lng_f,
                ft.FilledButton(
                    "Update My Location",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                        bgcolor=BRAND_PRIMARY,
                        padding=16,
                    ),
                    on_click=update_gps,
                ),
            ],
        ),
    ), refresh_logs
