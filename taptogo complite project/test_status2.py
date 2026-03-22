import traceback
import flet as ft
from screens.status_screen import build_status_screen

def main(page: ft.Page):
    try:
        view, refresh = build_status_screen(page, "user123", None)
        page.add(view)
        print("SUCCESS ADDING")
        page.window_destroy()
    except Exception as e:
        traceback.print_exc()
        page.window_destroy()

ft.app(target=main)
