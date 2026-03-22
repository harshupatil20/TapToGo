# TapToGo

**TapToGo** is a cross-platform NFC-based bus ticketing application built with [Flet](https://flet.dev/). Passengers tap in and tap out using NFC-enabled devices; fares are calculated automatically based on distance traveled. The app also includes an admin portal, conductor dashboard, camera-based crowd counting, and a Live Bus Chat feature.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [User Roles](#user-roles)
- [Configuration](#configuration)
- [Android Build & NFC](#android-build--nfc)
- [Fare Calculation](#fare-calculation)
- [Database](#database)
- [License](#license)

---

## Features

### Passenger Experience
- **NFC Tap In / Tap Out** — Tap your phone on bus NFC tags to start and end a trip
- **Home Dashboard** — Greeting, wallet balance, active trip card, and bus listings with AI seat availability predictor
- **Route View** — Live bus route with stop strip, ETA simulator, and map integration (optional)
- **Live Bus Chat** — Communicate with fellow passengers; includes Bus Status and Today's Insight (static demo)
- **Profile** — Edit name, email, phone; manage wallet; view tap history
- **Payment Flow** — Pay pending fare via wallet when balance is insufficient
- **Session Persistence** — Auto-login on app restart

### Admin Portal
- Add new buses with conductor and camera credentials
- View and manage all buses
- Configure fare settings (base fare, per-stop increment, max fare)

### Conductor Dashboard
- View bus details and today's boarding count
- Update bus GPS location manually
- Crowd prediction via image/video upload (uses ML model when available)
- Tap logs for the assigned bus

### Camera Portal
- Real-time crowd counting via webcam (CSRNet model)
- Updates bus occupancy (`people_count`) in the database

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | [Flet](https://flet.dev/) (Flutter-based) |
| Language | Python 3.10+ |
| Database | SQLite |
| NFC (Android) | Kotlin bridge + file polling |
| ML (optional) | PyTorch, torchvision, OpenCV (for crowd counting) |

---

## Project Structure

```
taptogo/
├── main.py                 # App entry, routing, role-based shells
├── db.py                   # SQLite helpers (users, buses, tap_logs, etc.)
├── fare_logic.py           # Fare calculation and config (fare_config.json)
├── constants.py            # Theme colors, stops, API keys, admin config
├── ui.py                   # Snackbar helpers
├── model_function.py       # ML crowd model (image, video, webcam)
│
├── screens/
│   ├── login.py            # Login (passenger, admin, conductor, camera)
│   ├── register.py         # Passenger registration
│   ├── home.py             # Passenger home with bus cards
│   ├── tap.py              # NFC Tap screen (poll nfc_scan.tmp)
│   ├── on_board.py         # In-trip view (Tap Out, map, stops)
│   ├── payment.py          # Pay pending fare
│   ├── live_chat.py        # Live Bus Chat + Status + Today's Insight
│   ├── route_screen.py     # Route tab with ETA, stops, map
│   ├── profile.py          # Profile, wallet, tap history
│   ├── bus_detail.py       # Bus stop list, schedule
│   │
│   ├── admin/
│   │   ├── admin_home.py   # Admin portal landing
│   │   ├── add_bus.py      # Add bus form
│   │   ├── view_buses.py   # List buses
│   │   └── fare_config.py  # Fare settings
│   │
│   ├── conductor/
│   │   └── conductor_dashboard.py
│   │
│   └── camera/
│       └── camera_portal.py
│
├── components/
│   ├── active_trip_card.py # Active trip summary card
│   ├── bus_card.py         # Bus listing card
│   ├── stop_chip.py        # Stop chip
│   └── wallet_chip.py      # Wallet balance chip
│
├── utils/
│   ├── map_html.py         # Leaflet map HTML (WebView)
│   └── eta_simulator.py    # Simulated stop ETAs
│
├── android/                # NFC integration for Android
│   ├── README.md           # NFC setup instructions
│   ├── MainActivity.kt     # NFC UID → nfc_scan.tmp
│   └── AndroidManifest_nfc_additions.xml
│
├── requirements.txt
├── pyproject.toml          # Flet project config (org: com.taptogo)
├── fare_config.json        # Generated fare settings
└── taptogo.db              # SQLite DB (created on first run)
```

---

## Prerequisites

- **Python 3.10+**
- **Flet** — `pip install flet`
- **Optional (crowd model):** `torch`, `torchvision`, `opencv-python`
- **Optional (map):** `flet-webview`, `GOOGLE_MAPS_API_KEY` env var

---

## Installation

1. **Clone or download** the project:
   ```bash
   cd taptogo
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   For minimal install (no ML):
   ```bash
   pip install "flet>=0.24.0"
   ```

---

## Running the App

From the project root (parent of `taptogo` folder):

```bash
cd taptogo
flet run main.py
```

Or:

```bash
python -m flet run taptogo/main.py
```

The app opens in a desktop window (or web, depending on Flet config). On first run, SQLite creates `taptogo.db` in the `taptogo` directory.

---

## User Roles

| Role | Login | Description |
|------|-------|-------------|
| **Passenger** | Email + password (from register) | Tap in/out, view routes, chat, profile |
| **Admin** | `harmetadv` / `12345678` (see `constants.py`) | Add buses, view buses, fare config |
| **Conductor** | Conductor ID + password (from admin when adding bus) | Dashboard, location, crowd prediction |
| **Camera** | Camera ID + password (from admin) | Webcam crowd counting |

---

## Configuration

### constants.py
- `ADMIN_ID` / `ADMIN_PASSWORD` — Admin login
- `THANE_STOPS` — Default bus route stops
- `GOOGLE_MAPS_API_KEY` — For static maps (optional)
- `get_nfc_tmp_paths()` — Paths checked for NFC scan file

### fare_config.json (auto-generated)
- `base_fare` — Minimum fare (₹)
- `per_stop_increment` — Fare per stop
- `max_fare` — Maximum fare cap

### fare_logic.py
- `calculate_fare(tap_in_stop, tap_out_stop, route_stops)` — Distance-based fare
- Config loaded from `fare_config.json`; falls back to defaults if missing

---

## Android Build & NFC

See `android/README.md` for:

1. Adding NFC permission and intent filters to `AndroidManifest.xml`
2. Replacing `MainActivity.kt` with the NFC-aware version
3. Kotlin writes NFC tag UID to `filesDir/nfc_scan.tmp`; Flet Tap screen polls this file

Build APK:
```bash
cd taptogo
flet build apk
```

---

## Fare Calculation

Formula (from `fare_logic.py`):

```
fare = base_fare + (num_stops × per_stop_increment)
fare = min(max_fare, max(base_fare, fare))
```

- Stops are derived from the bus route's `stops` list.
- `tap_in_stop` and `tap_out_stop` must exist in the route; otherwise `base_fare` is used.

---

## Database

SQLite file: `taptogo/taptogo.db`

### Main Tables
- **users** — Passengers (name, email, phone, password, wallet_balance, payment state)
- **buses** — Bus info, stops, schedule, conductor, camera, NFC signature, GPS
- **conductors** — Conductor ID, password, bus_id
- **cameras** — Camera ID, password, bus_id, stream_active
- **tap_logs** — user_id, bus_id, timestamp, action (tap_in/tap_out), from_stop, to_stop, fare

NFC matching: buses are matched by `nfc_tag_signature` (exact or normalized UID).

---

## License

Proprietary. Use as permitted by the project owner.
