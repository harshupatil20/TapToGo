import os
from pathlib import Path

ADMIN_ID = "harmetadv"

# NFC bridge: Kotlin writes UID here, Python polls. On Android use app files dir.
NFC_TMP_FILE = "nfc_scan.tmp"


def get_nfc_tmp_paths() -> list[Path]:
    """Paths to check for NFC scan file. Kotlin writes to filesDir on Android (≈ cwd)."""
    base = Path(__file__).parent.parent
    return [
        Path.cwd() / NFC_TMP_FILE,
        base / NFC_TMP_FILE,
        Path.home() / NFC_TMP_FILE,
        Path(os.environ.get("ANDROID_APP_PATH", ".")) / NFC_TMP_FILE,
    ]


ADMIN_PASSWORD = "12345678"

FARE_PER_STOP = 5
MIN_FARE = 5

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

THANE_STOPS = [
    "Thane Station",
    "Kopri",
    "Cadbury Junction",
    "Majiwada",
    "Manpada",
    "Ghodbunder Road",
    "Kapurbawdi",
    "Dhokali",
    "Kolbad",
    "Naupada",
    "Charai",
    "Jambli Naka",
    "Wagle Estate",
    "Rabodi",
    "Shivaji Nagar",
    "Kalwa",
    "Mumbra",
    "Diva",
    "Bhiwandi",
    "Balkum",
    "Hiranandani Estate",
    "Brahmand",
    "Owale",
    "Patlipada",
    "Vasant Vihar",
    "Ambedkar Nagar",
    "Ram Maruti Road",
    "Ghantali",
    "Teen Haath Naka",
    "Talao Pali",
    "Masunda Lake",
    "Upvan Lake",
    "Yeoor",
    "Kasheli",
    "Anjur Phata",
    "Dawale",
    "Rajnoli",
    "Ghod Bunder Fort",
    "Gaimukh",
    "Kolshet",
    "Pokhran Road No 1",
    "Pokhran Road No 2",
    "Anand Nagar",
    "Savarkar Nagar",
    "Uthalsar",
    "Lal Bahadur Shastri Road",
    "Eastern Express Highway (Thane)",
    "Balkum Naka",
    "Mumbra Bypass",
    "Kausa",
]

BRAND_PRIMARY = "#5B6FFF"
BRAND_SECONDARY = "#A259FF"
ACCENT_TEAL = "#00E5CC"
ACCENT_AMBER = "#F5A623"
BG_PAGE = "#0D1117"
BG_CARD = "#161B27"
BG_CARD_ELEVATED = "#1C2333"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#8B9AB0"
RADIUS_CARD = 16
RADIUS_PILL = 999

# Gradient colors for buttons (use ShaderMask or Container gradient trick)
GRAD_START = "#5B6FFF"
GRAD_END = "#A259FF"


def calculate_fare(tap_in_stop: str, tap_out_stop: str, route_stops: list) -> float:
    if not route_stops or tap_in_stop not in route_stops or tap_out_stop not in route_stops:
        return float(MIN_FARE)
    i = route_stops.index(tap_in_stop)
    j = route_stops.index(tap_out_stop)
    segments = abs(j - i)
    return max(float(MIN_FARE), float(segments * FARE_PER_STOP))
