"""
fare_logic.py — Reusable fare calculation for Tap2Go.
Base fare + distance-based increment. Max fare capped at ₹45.
"""
from __future__ import annotations

import json
from pathlib import Path

# ===== FARE CONFIG START =====
# Config file path (same dir as this module)
FARE_CONFIG_PATH = Path(__file__).parent / "fare_config.json"

DEFAULT_CONFIG = {
    "base_fare": 10,
    "per_stop_increment": 2,
    "max_fare": 45,
}


def _load_config() -> dict:
    """Load fare config from JSON file. Falls back to defaults if missing."""
    try:
        if FARE_CONFIG_PATH.exists():
            data = json.loads(FARE_CONFIG_PATH.read_text(encoding="utf-8"))
            return {
                "base_fare": int(data.get("base_fare", DEFAULT_CONFIG["base_fare"])),
                "per_stop_increment": int(data.get("per_stop_increment", DEFAULT_CONFIG["per_stop_increment"])),
                "max_fare": int(data.get("max_fare", DEFAULT_CONFIG["max_fare"])),
            }
    except (json.JSONDecodeError, OSError, TypeError):
        pass
    return dict(DEFAULT_CONFIG)


def _save_config(config: dict) -> None:
    """Save fare config to JSON file."""
    try:
        FARE_CONFIG_PATH.write_text(
            json.dumps(config, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def get_fare_config() -> dict:
    """Return current fare config (base_fare, per_stop_increment, max_fare)."""
    return _load_config()


def set_fare_config(base_fare: int = None, per_stop_increment: int = None, max_fare: int = None) -> dict:
    """Update fare config. Returns updated config."""
    cfg = _load_config()
    if base_fare is not None:
        cfg["base_fare"] = max(0, int(base_fare))
    if per_stop_increment is not None:
        cfg["per_stop_increment"] = max(0, int(per_stop_increment))
    if max_fare is not None:
        cfg["max_fare"] = max(0, int(max_fare))
    _save_config(cfg)
    return cfg


def calculate_fare(tap_in_stop: str, tap_out_stop: str, route_stops: list) -> float:
    """
    Calculate fare between two stops on a route.
    Formula: base_fare + (num_stops * per_stop_increment), capped at max_fare.
    """
    if not route_stops or tap_in_stop not in route_stops or tap_out_stop not in route_stops:
        cfg = _load_config()
        return float(cfg["base_fare"])

    i = route_stops.index(tap_in_stop)
    j = route_stops.index(tap_out_stop)
    num_stops = abs(j - i)
    if num_stops == 0:
        cfg = _load_config()
        return float(cfg["base_fare"])

    cfg = _load_config()
    base = float(cfg["base_fare"])
    inc = float(cfg["per_stop_increment"])
    cap = float(cfg["max_fare"])

    fare = base + (num_stops * inc)
    return min(cap, max(base, fare))


# ===== FARE CONFIG END =====
