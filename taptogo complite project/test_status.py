import traceback
from screens.status_screen import build_status_screen

class DummyPage:
    def __init__(self):
        self.width = 400
        self.height = 800
    def update(self): pass
    def run_task(self, t): pass

page = DummyPage()
try:
    build_status_screen(page, "user123", {"bus_id": "B1", "tap_in": "Stop A", "dest": "Stop B"})
    print("SUCCESS TRIP")
except Exception as e:
    traceback.print_exc()
