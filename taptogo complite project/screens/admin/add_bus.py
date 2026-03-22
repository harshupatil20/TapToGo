import uuid

import flet as ft

from constants import BG_PAGE, BG_CARD, BG_CARD_ELEVATED, BRAND_PRIMARY, RADIUS_CARD, RADIUS_PILL, TEXT_MUTED, TEXT_WHITE, THANE_STOPS
import db
from ui import snackbar_error, snackbar_ok


_INPUT_STYLE = {
    "border_radius": RADIUS_CARD,
    "filled": True,
    "bgcolor": BG_CARD_ELEVATED,
    "border_color": "rgba(255,255,255,0.12)",
    "color": TEXT_WHITE,
    "cursor_color": BRAND_PRIMARY,
    "label_style": ft.TextStyle(color=TEXT_MUTED, size=12),
    "hint_style": ft.TextStyle(color=TEXT_MUTED, size=14),
}


def build_add_bus(page, on_back, existing_id: str | None = None):
    bus_no = ft.TextField(label="Bus Number", **_INPUT_STYLE)
    bus_name = ft.TextField(label="Bus Name", **_INPUT_STYLE)
    cond_name = ft.TextField(label="Conductor Name", **_INPUT_STYLE)
    cond_id = ft.TextField(label="Conductor ID", **_INPUT_STYLE)
    cond_pw = ft.TextField(label="Conductor Password", password=True, can_reveal_password=True, **_INPUT_STYLE)
    cam_id = ft.TextField(label="Camera ID", **_INPUT_STYLE)
    cam_pw = ft.TextField(label="Camera Password", password=True, can_reveal_password=True, **_INPUT_STYLE)
    nfc = ft.TextField(
        label="NFC Tag Signature",
        hint_text="Paste UID from NFC Tools app",
        helper="Use NFC Tools app to read your sticker UID and paste it here",
        helper_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        **_INPUT_STYLE,
    )

    search = ft.TextField(
        label="Search stops",
        hint_text="Type to filter...",
        **_INPUT_STYLE,
    )
    pick_col = ft.Column(spacing=8)
    chips_row = ft.Column(spacing=8)
    schedule_col = ft.Column(spacing=10)

    selected: list[str] = []
    times: list[str] = []

    def render_chips():
        chips_row.controls.clear()
        for i, s in enumerate(selected):
            chips_row.controls.append(
                ft.Container(
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.12, BRAND_PRIMARY),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Text(s, size=12, color=TEXT_WHITE),
                            ft.IconButton(
                                ft.Icons.ARROW_UPWARD_ROUNDED,
                                icon_size=18,
                                icon_color=TEXT_WHITE,
                                on_click=lambda e, idx=i: move(idx, -1),
                            ),
                            ft.IconButton(
                                ft.Icons.ARROW_DOWNWARD_ROUNDED,
                                icon_size=18,
                                icon_color=TEXT_WHITE,
                                on_click=lambda e, idx=i: move(idx, 1),
                            ),
                        ],
                    ),
                )
            )
        page.update()

    def move(i: int, delta: int):
        j = i + delta
        if j < 0 or j >= len(selected):
            return
        selected[i], selected[j] = selected[j], selected[i]
        render_chips()

    def toggle_stop(name: str, add: bool):
        if add:
            if name not in selected:
                selected.append(name)
        else:
            if name in selected:
                selected.remove(name)
        render_chips()

    def render_picker():
        q = (search.value or "").lower()
        pick_col.controls.clear()
        for s in THANE_STOPS:
            if q and q not in s.lower():
                continue
            pick_col.controls.append(
                ft.Checkbox(
                    label=s,
                    value=s in selected,
                    on_change=lambda e, stop=s: toggle_stop(stop, e.control.value),
                    fill_color=BRAND_PRIMARY,
                    check_color=TEXT_WHITE,
                    label_style=ft.TextStyle(color=TEXT_WHITE, size=14),
                )
            )
        page.update()

    def add_time(_):
        tf = ft.TextField(
            label="Time (HH:MM)",
            hint_text="08:30",
            **_INPUT_STYLE,
        )

        def save_slot(__):
            slot = (tf.value or "").strip() or "09:00"
            times.append(slot)
            page.pop_dialog()
            render_times()

        dlg = ft.AlertDialog(
            bgcolor=BG_CARD,
            title=ft.Text("Add departure", color=TEXT_WHITE),
            content=tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog(), style=ft.ButtonStyle(color=TEXT_MUTED)),
                ft.FilledButton("Add", on_click=save_slot, style=ft.ButtonStyle(bgcolor=BRAND_PRIMARY)),
            ],
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        )
        page.show_dialog(dlg)

    def render_times():
        schedule_col.controls.clear()
        for i, t in enumerate(times):
            schedule_col.controls.append(
                ft.Container(
                    border_radius=RADIUS_CARD,
                    bgcolor=BG_CARD_ELEVATED,
                    padding=12,
                    border=ft.border.all(1, "rgba(255,255,255,0.08)"),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(t, size=14, color=TEXT_WHITE),
                            ft.IconButton(ft.Icons.CLOSE_ROUNDED, icon_color=TEXT_MUTED, on_click=lambda e, idx=i: remove_time(idx)),
                        ],
                    ),
                )
            )
        page.update()

    def remove_time(idx: int):
        if 0 <= idx < len(times):
            times.pop(idx)
            render_times()

    search.on_change = lambda _: render_picker()

    def load_existing():
        if not existing_id:
            render_picker()
            return
        try:
            b = db.get_bus(existing_id)
            if not b:
                return
            bus_no.value = str(b.get("bus_no") or "")
            bus_name.value = str(b.get("bus_name") or "")
            cond_name.value = str(b.get("conductor_name") or "")
            cond_id.value = str(b.get("conductor_id") or "")
            cond_pw.value = str(b.get("conductor_password") or "")
            cam_id.value = str(b.get("camera_id") or "")
            cam_pw.value = str(b.get("camera_password") or "")
            nfc.value = str(b.get("nfc_tag_signature") or "")
            selected.clear()
            selected.extend(list(b.get("stops") or []))
            times.clear()
            times.extend(list(b.get("schedule") or []))
            render_chips()
            render_times()
            render_picker()
        except Exception as e:
            snackbar_error(page, str(e))

    def submit(_):
        if not selected:
            snackbar_error(page, "Select at least one stop.")
            return
        bid = existing_id or f"bus_{uuid.uuid4().hex[:10]}"
        try:
            if existing_id:
                db.update_bus(
                    bid,
                    bus_no=bus_no.value or "",
                    bus_name=bus_name.value or "",
                    stops=selected,
                    schedule=times,
                    conductor_name=cond_name.value or "",
                    conductor_id=cond_id.value or "",
                    conductor_password=cond_pw.value or "",
                    camera_id=cam_id.value or "",
                    camera_password=cam_pw.value or "",
                    nfc_tag_signature=nfc.value or "",
                )
                cid = cond_id.value or ""
                cam = cam_id.value or ""
                if cid:
                    db.upsert_conductor(cid, cond_pw.value or "", bid)
                if cam:
                    db.upsert_camera(cam, cam_pw.value or "", bid)
            else:
                db.create_bus(
                    bus_id=bid,
                    bus_no=bus_no.value or "",
                    bus_name=bus_name.value or "",
                    stops=selected,
                    schedule=times,
                    conductor_name=cond_name.value or "",
                    conductor_id=cond_id.value or "",
                    conductor_password=cond_pw.value or "",
                    camera_id=cam_id.value or "",
                    camera_password=cam_pw.value or "",
                    nfc_tag_signature=nfc.value or "",
                )
            snackbar_ok(page, "Bus saved.")
            on_back()
        except Exception as e:
            snackbar_error(page, str(e))

    def delete_bus(_):
        if not existing_id:
            return
        try:
            db.delete_bus(existing_id)
            snackbar_ok(page, "Bus removed.")
            on_back()
        except Exception as e:
            snackbar_error(page, str(e))

    load_existing()

    form_column = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(ft.Icons.ARROW_BACK_ROUNDED, on_click=lambda _: on_back()),
                    ft.Text("Add Bus" if not existing_id else "Edit Bus", size=22, weight=ft.FontWeight.W_700, color=BRAND_PRIMARY),
                ]
            ),
            bus_no,
            bus_name,
            ft.Text("Stops (multi-select)", size=14, color=TEXT_MUTED),
            search,
            ft.Container(
                border_radius=RADIUS_CARD,
                bgcolor=BG_CARD,
                padding=10,
                border=ft.border.all(1, "rgba(255,255,255,0.08)"),
                content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=[pick_col]),
            ),
            ft.Text("Route order", size=14, color=TEXT_MUTED),
            chips_row,
            ft.Text("Schedule", size=14, color=TEXT_MUTED),
            ft.OutlinedButton(
                "Add time slot",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                    color=BRAND_PRIMARY,
                    side=ft.BorderSide(1, BRAND_PRIMARY),
                ),
                on_click=add_time,
            ),
            schedule_col,
            cond_name,
            cond_id,
            cond_pw,
            cam_id,
            cam_pw,
            nfc,
            ft.FilledButton(
                "Submit",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PILL),
                    bgcolor=BRAND_PRIMARY,
                    padding=16,
                ),
                on_click=submit,
            ),
            ft.TextButton("Delete bus", on_click=delete_bus, visible=existing_id is not None, style=ft.ButtonStyle(color="#FF4D4D")),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=16,
    )
    return ft.Container(
        expand=True,
        bgcolor=BG_PAGE,
        padding=20,
        content=form_column,
    )
