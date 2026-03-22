import traceback
import flet as ft
from screens.status_screen import build_status_screen
import db

def main():
    page = ft.Page('inmem')
    users = db.list_users() or []
    print(f"Testing {len(users)} users...")
    for u in users:
        uid = u.get("id")
        trip = db.get_active_trip(str(uid))
        try:
            view, ref = build_status_screen(page, uid, trip)
        except Exception as e:
            print(f"CRASH on user {uid}!")
            traceback.print_exc()
            return
            
    print("ALL USERS PASSED")

if __name__ == "__main__":
    main()
