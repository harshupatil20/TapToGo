import time
import traceback
import flet as ft
from screens.status_screen import build_status_screen

def main(page: ft.Page):
    try:
        view, refresh = build_status_screen(page, "user123", None)
        page.add(view)
        print("SUCCESS ADDING")
        time.sleep(2)
        page.window_close()
    except Exception as e:
        traceback.print_exc()

ft.app(target=main)
