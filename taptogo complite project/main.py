import flet as ft

from constants import BG_PAGE, BG_CARD, BRAND_PRIMARY, BRAND_SECONDARY, TEXT_MUTED, TEXT_WHITE, GRAD_START, GRAD_END
from db import init_db
from ui import snackbar_error
from screens.admin.add_bus import build_add_bus
from screens.admin.admin_home import build_admin_home
from screens.admin.fare_config import build_fare_config
from screens.admin.view_buses import build_view_buses
from screens.bus_detail import build_bus_detail
from screens.camera.camera_portal import build_camera_portal
from screens.conductor.conductor_dashboard import build_conductor_dashboard
from screens.home import build_home
from screens.login import build_login
from screens.on_board import build_on_board
from screens.payment import build_payment
from screens.live_chat import build_live_chat
from screens.profile import build_profile
from screens.register import build_register
from screens.route_screen import build_route_screen
from screens.tap import build_tap

init_db()


def main(page: ft.Page):
    page.title = "TapToGo"
    page.bgcolor = BG_PAGE
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=BRAND_PRIMARY)
    page.theme_mode = ft.ThemeMode.DARK

    st = {
        "role": None,
        "uid": None,
        "tab": 0,
        "trip": None,
        "bus_detail": None,
        "from_stop": "",
        "to_stop": "",
        "payment_ctx": {},
        "admin_sub": "home",
        "conductor": {},
        "camera": {},
        "refreshers": [],
    }

    def clear_refreshers():
        st["refreshers"].clear()

    def mount(c):
        page.controls.clear()
        page.add(ft.SafeArea(ft.Container(content=c, expand=True), expand=True))
        page.update()

    def try_restore_session():
        try:
            uid = page.client_storage.get("user_id")
            if uid is not None:
                import db
                u = db.get_user(uid)
                if u:
                    st["uid"] = int(uid)
                    st["role"] = "passenger"
                    return True
        except Exception:
            pass
        return False

    def persist_session():
        try:
            if st.get("uid") is not None:
                page.client_storage.set("user_id", str(st["uid"]))
        except Exception:
            pass

    def clear_session():
        try:
            page.client_storage.remove("user_id")
        except Exception:
            pass

    def passenger_payment_pending() -> bool:
        if st.get("role") != "passenger" or st.get("uid") is None:
            return False
        import db
        u = db.get_user(st["uid"])
        return bool((u or {}).get("payment_pending"))

    def logout_passenger():
        clear_session()
        st["role"] = None
        st["uid"] = None
        st["trip"] = None
        st["tab"] = 0
        st["bus_detail"] = None
        show_login()

    def show_payment_forced(ctx=None):
        clear_refreshers()

        def done_home():
            st["payment_ctx"] = {}
            show_passenger_shell()

        pay, refresh = build_payment(page, st["uid"], ctx or st.get("payment_ctx") or {}, done_home)
        st["refreshers"] = [refresh]
        mount(pay)
        refresh()

    def show_passenger_shell():
        clear_refreshers()
        if passenger_payment_pending():
            st["payment_ctx"] = {}
            show_payment_forced({})
            return

        def paint():
            clear_refreshers()
            if passenger_payment_pending():
                st["payment_ctx"] = {}
                show_payment_forced({})
                return

            nav_index = st["tab"]
            trip = st.get("trip")
            bd = st.get("bus_detail")

            def go_bus_detail(bus_id, from_s, to_s):
                st["bus_detail"] = bus_id
                st["from_stop"] = from_s or ""
                st["to_stop"] = to_s or ""
                paint()

            def back_from_detail():
                st["bus_detail"] = None
                paint()

            # ===== TAP STATE FIX START =====
            def on_onboard(bus_id, bus, tap_in, dest):
                st["trip"] = {
                    "bus_id": bus_id,
                    "bus": bus,
                    "tap_in": tap_in,
                    "dest": dest,
                }
                st["tab"] = 2   # Stay on Tap tab to show Tap Out screen
                paint()
                try:
                    page.update()
                except Exception:
                    pass
            # ===== TAP STATE FIX END =====

            def on_need_payment(ctx):
                st["payment_ctx"] = ctx
                st["trip"] = None
                show_payment_forced(ctx)

            body = ft.Container(expand=True)

            def _placeholder(icon, label="Coming Soon", sub="This section is under development"):
                return ft.Container(
                    expand=True,
                    bgcolor="#0D1117",
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, size=48, color="#8B9AB0"),
                            ft.Text(label, size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            ft.Text(sub, size=13, color="#8B9AB0"),
                        ],
                    ),
                )

            if nav_index == 0:          # Home
                home, refresh = build_home(
                    page,
                    st["uid"],
                    go_bus_detail,
                    bus_detail_id=bd,
                    on_back_from_bus=back_from_detail,
                    trip=None,
                    from_stop=st.get("from_stop") or "",
                    to_stop=st.get("to_stop") or "",
                )
                st["refreshers"] = [refresh]
                body.content = home
                refresh()
            elif nav_index == 1:          # Live Chat (merged with Status)
                body.content = build_live_chat(page, st["uid"], trip)
            elif nav_index == 2:          # Tap (center)
                if trip:
                    ob, _stop = build_on_board(
                        page,
                        st["uid"],
                        trip["bus_id"],
                        trip["bus"],
                        trip["tap_in"],
                        trip["dest"],
                        on_need_payment,
                    )
                    body.content = ob
                else:
                    body.content = build_tap(page, st["uid"], on_onboard)
            elif nav_index == 3:          # Route
                route_view, refresh = build_route_screen(page, st["uid"], st.get("trip"))
                st["refreshers"] = [refresh]
                body.content = route_view
                refresh()
            else:                        # Profile (index 4)
                prof, refresh = build_profile(page, st["uid"], logout_passenger)
                st["refreshers"] = [refresh]
                body.content = prof
                refresh()

            # ===== GENERAL STABILITY START =====
            def on_nav(idx: int):
                st["tab"] = int(idx)
                paint()
                try:
                    page.update()
                except Exception:
                    pass
            # ===== GENERAL STABILITY END =====

            def bottom_nav():
                # 5 tabs: Home | Live Chat | Tap(center) | Route | Profile
                _ACTIVE   = "#7C3AED"
                _INACTIVE = "#8B9AB0"
                _NAV_BG   = "#161B27"
                _GRAD_A   = "#3B82F6"
                _GRAD_B   = "#7C3AED"

                tab_defs = [
                    ("Home",      ft.Icons.HOME_ROUNDED,          0),
                    ("Live Chat", ft.Icons.CHAT_BUBBLE_OUTLINE,   1),
                    (None,        ft.Icons.NFC_ROUNDED,           2),   # center Tap
                    ("Route",     ft.Icons.MAP_ROUNDED,           3),
                    ("Profile",   ft.Icons.PERSON_ROUNDED,        4),
                ]

                def _tab_item(label, icon, idx):
                    is_center = label is None
                    selected  = nav_index == idx

                    if is_center:
                        # Elevated circular button that floats above the bar
                        circle = ft.Container(
                            width=56, height=56,
                            border_radius=999,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.Alignment(-1, -1),
                                end=ft.alignment.Alignment(1, 1),
                                colors=[_GRAD_A, _GRAD_B],
                            ),
                            shadow=ft.BoxShadow(
                                blur_radius=20,
                                color=ft.Colors.with_opacity(0.5, _GRAD_B),
                                offset=ft.Offset(0, 4),
                            ),
                            alignment=ft.alignment.Alignment(0, 0),
                            content=ft.Icon(icon, color=TEXT_WHITE, size=28),
                        )
                        return ft.GestureDetector(
                            on_tap=lambda e, i=idx: on_nav(i),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.END,
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        content=circle,
                                        margin=ft.margin.only(bottom=6),
                                    ),
                                    ft.Text("Tap", size=11,
                                            color=TEXT_WHITE if selected else _INACTIVE,
                                            weight=ft.FontWeight.W_600),
                                ],
                            ),
                        )

                    icon_col = _ACTIVE if selected else _INACTIVE
                    return ft.GestureDetector(
                        on_tap=lambda e, i=idx: on_nav(i),
                        content=ft.Container(
                            expand=True,
                            alignment=ft.alignment.Alignment(0, 0),
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=3,
                                controls=[
                                    ft.Icon(icon, color=icon_col, size=24),
                                    ft.Text(label, size=11, color=icon_col,
                                            weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400),
                                ],
                            ),
                        ),
                    )

                return ft.Container(
                    height=65,
                    bgcolor=_NAV_BG,
                    border=ft.border.only(
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.06, TEXT_WHITE))
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[_tab_item(lbl, ico, i) for lbl, ico, i in tab_defs],
                    ),
                )

            shell = ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(expand=True, content=body),
                    bottom_nav(),
                ],
            )
            mount(shell)

        paint()

    def show_login():
        clear_refreshers()
        st["role"] = None
        st["uid"] = None

        def on_in(role, payload=None):
            payload = payload or {}
            if role == "register":
                mount(
                    build_register(
                        page,
                        lambda: show_login(),
                    )
                )
                return
            if role == "admin":
                st["role"] = "admin"
                st["admin_sub"] = "home"
                show_admin()
                return
            if role == "conductor":
                st["role"] = "conductor"
                st["conductor"] = payload
                show_conductor()
                return
            if role == "camera":
                st["role"] = "camera"
                st["camera"] = payload
                show_camera()
                return
            if role == "passenger":
                st["role"] = "passenger"
                st["uid"] = payload.get("id")
                persist_session()
                from screens.login_animation import build_login_animation
                import asyncio

                async def run_splash():
                    await build_login_animation(
                        page,
                        lambda: (show_payment_forced({}) if passenger_payment_pending() else show_passenger_shell()),
                    )

                page.run_task(run_splash)
                return

        mount(build_login(page, on_in))

    def show_admin():
        clear_refreshers()

        def logout():
            st["role"] = None
            show_login()

        def add_bus():
            st["admin_sub"] = "add"
            render_admin()

        def view_buses():
            st["admin_sub"] = "list"
            render_admin()

        def fare_config():
            st["admin_sub"] = "fare"
            render_admin()

        def back_home():
            st["admin_sub"] = "home"
            render_admin()

        def edit_bus(bus_id: str):
            st["admin_edit"] = bus_id
            st["admin_sub"] = "edit"
            render_admin()

        def render_admin():
            if st["admin_sub"] == "home":
                mount(
                    build_admin_home(
                        page,
                        add_bus,
                        view_buses,
                        fare_config,
                        logout,
                    )
                )
            elif st["admin_sub"] == "add":
                mount(build_add_bus(page, back_home, None))
            elif st["admin_sub"] == "list":
                view, refresh = build_view_buses(page, back_home, edit_bus)
                st["refreshers"] = [refresh]
                mount(view)
                refresh()
            elif st["admin_sub"] == "edit":
                bid = st.get("admin_edit")
                mount(build_add_bus(page, back_home, bid))
            elif st["admin_sub"] == "fare":
                mount(build_fare_config(page, back_home))

        render_admin()

    def show_conductor():
        clear_refreshers()
        bus_id = (st.get("conductor") or {}).get("bus_id")
        name = (st.get("conductor") or {}).get("name", "")
        if not bus_id:
            snackbar_error(page, "No bus linked.")
            show_login()
            return

        def logout():
            st["role"] = None
            show_login()

        dash, refresh = build_conductor_dashboard(page, bus_id, name)
        st["refreshers"] = [refresh]

        def wrapped():
            mount(
                ft.Column(
                    expand=True,
                    controls=[
                        dash,
                        ft.TextButton("Logout", on_click=lambda _: logout()),
                    ],
                )
            )
            refresh()

        wrapped()

    def show_camera():
        clear_refreshers()
        cam_id = (st.get("camera") or {}).get("camera_id")
        bus_id = (st.get("camera") or {}).get("bus_id")
        if not cam_id or not bus_id:
            snackbar_error(page, "Invalid camera session.")
            show_login()
            return

        def offline():
            st["role"] = None
            show_login()

        mount(build_camera_portal(page, cam_id, bus_id, offline))

    def on_resume(e: ft.AppLifecycleStateChangeEvent):
        if e.state == ft.AppLifecycleState.RESUME and st.get("role") == "passenger" and st.get("uid"):
            if passenger_payment_pending():
                show_payment_forced({})

    page.on_app_lifecycle_state_change = on_resume

    def bootstrap():
        if try_restore_session():
            if passenger_payment_pending():
                show_payment_forced({})
            else:
                show_passenger_shell()
        else:
            show_login()

    bootstrap()


if __name__ == "__main__":
    ft.run(main)
