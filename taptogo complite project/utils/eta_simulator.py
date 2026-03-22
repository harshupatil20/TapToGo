"""
utils/eta_simulator.py — Simulated ETA logic for bus stops.
Assign estimated arrival times and update dynamically.
"""
from __future__ import annotations

import datetime

# ===== TIME SLOT / ETA MANAGEMENT START =====

MINS_PER_STOP = 3  # Simulated: ~3 min between stops


def get_stop_etas(stops: list, current_stop_idx: int, base_time: datetime.datetime = None) -> list[tuple[str, str]]:
    """
    Return list of (stop_name, eta_str) for each stop.
    ETA is relative to current position - past stops show "Departed", future show "X min".
    """
    if not stops:
        return []
    base = base_time or datetime.datetime.now()
    result = []
    for i in range(len(stops)):
        if i < current_stop_idx:
            result.append((stops[i], "Departed"))
        elif i == current_stop_idx:
            result.append((stops[i], "Now"))
        else:
            mins = (i - current_stop_idx) * MINS_PER_STOP
            result.append((stops[i], f"{mins} min"))
    return result


def get_eta_for_stop(stops: list, current_stop_idx: int, target_stop: str) -> str:
    """Get ETA string for a specific stop (e.g. user's destination)."""
    if not stops or target_stop not in stops:
        return "—"
    cur = max(0, min(current_stop_idx, len(stops) - 1))
    idx = stops.index(target_stop)
    if idx <= cur:
        return "Now" if idx == cur else "Departed"
    return f"{(idx - cur) * MINS_PER_STOP} min"


# ===== TIME SLOT / ETA MANAGEMENT END =====
