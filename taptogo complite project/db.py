"""
SQLite database helper for TapToGo.
All DB operations go through this module.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).parent / "taptogo.db"
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH))
        _conn.row_factory = sqlite3.Row
    return _conn


def init_db() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            email TEXT UNIQUE NOT NULL,
            phone TEXT DEFAULT '',
            password TEXT NOT NULL,
            wallet_balance REAL DEFAULT 0,
            current_bus_id TEXT,
            tap_in_stop TEXT,
            tap_in_time TEXT,
            payment_pending INTEGER DEFAULT 0,
            pending_fare REAL DEFAULT 0,
            pending_to_stop TEXT
        );

        CREATE TABLE IF NOT EXISTS buses (
            id TEXT PRIMARY KEY,
            bus_no TEXT,
            bus_name TEXT,
            stops TEXT,
            schedule TEXT,
            conductor_name TEXT,
            conductor_id TEXT,
            conductor_password TEXT,
            camera_id TEXT,
            camera_password TEXT,
            nfc_tag_signature TEXT,
            current_lat REAL DEFAULT 19.2183,
            current_lng REAL DEFAULT 72.9781,
            people_count INTEGER DEFAULT 0,
            people_count_min INTEGER,
            people_count_max INTEGER
        );

        CREATE TABLE IF NOT EXISTS conductors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conductor_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bus_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cameras (
            camera_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            bus_id TEXT NOT NULL,
            stream_active INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tap_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            bus_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            from_stop TEXT,
            to_stop TEXT,
            fare_deducted REAL DEFAULT 0,
            payment_method TEXT
        );
    """)
    conn.commit()


# --- Users ---
def get_user(uid: int | str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (str(uid),)).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_email(email: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _row_to_dict(row) if row else None


def create_user(name: str, email: str, phone: str, password: str) -> int:
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO users (name, email, phone, password, wallet_balance,
           current_bus_id, tap_in_stop, tap_in_time, payment_pending, pending_fare, pending_to_stop)
           VALUES (?, ?, ?, ?, 0, NULL, '', '', 0, 0, '')""",
        (name, email, phone, password),
    )
    conn.commit()
    return cur.lastrowid


def update_user(uid: int | str, **kwargs: Any) -> None:
    if not kwargs:
        return
    conn = _get_conn()
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [str(uid)]
    conn.execute(f"UPDATE users SET {cols} WHERE id = ?", vals)
    conn.commit()


def verify_user(email: str, password: str) -> Optional[dict]:
    u = get_user_by_email(email)
    if u and u.get("password") == password:
        return u
    return None


# --- Buses ---
def get_bus(bus_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM buses WHERE id = ?", (bus_id,)).fetchone()
    return _bus_row_to_dict(row) if row else None


def get_bus_by_nfc(nfc_signature: str) -> Optional[dict]:
    """Match bus by NFC UID. Tries exact match, then normalized (uppercase, no colons)."""
    if not nfc_signature or not nfc_signature.strip():
        return None
    sig = nfc_signature.strip().upper()
    sig_normalized = sig.replace(":", "")
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM buses WHERE TRIM(UPPER(nfc_tag_signature)) = ?", (sig,)
    ).fetchone()
    if row:
        return _bus_row_to_dict(row)
    rows = conn.execute("SELECT * FROM buses").fetchall()
    for r in rows:
        stored = (r["nfc_tag_signature"] or "").strip().upper().replace(":", "")
        if stored == sig_normalized:
            return _bus_row_to_dict(r)
    return None


def list_buses() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM buses").fetchall()
    return [_bus_row_to_dict(r) for r in rows]


def create_bus(
    bus_id: str,
    bus_no: str,
    bus_name: str,
    stops: list,
    schedule: list,
    conductor_name: str,
    conductor_id: str,
    conductor_password: str,
    camera_id: str,
    camera_password: str,
    nfc_tag_signature: str,
) -> None:
    conn = _get_conn()
    conn.execute(
        """INSERT INTO buses (id, bus_no, bus_name, stops, schedule,
           conductor_name, conductor_id, conductor_password, camera_id, camera_password,
           nfc_tag_signature, people_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            bus_id,
            bus_no,
            bus_name,
            json.dumps(stops),
            json.dumps(schedule),
            conductor_name,
            conductor_id,
            conductor_password,
            camera_id,
            camera_password,
            nfc_tag_signature,
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO conductors (conductor_id, password, bus_id) VALUES (?, ?, ?)",
        (conductor_id, conductor_password, bus_id),
    )
    conn.execute(
        "INSERT OR REPLACE INTO cameras (camera_id, password, bus_id, stream_active) VALUES (?, ?, ?, 0)",
        (camera_id, camera_password, bus_id),
    )
    conn.commit()


def update_bus(bus_id: str, **kwargs: Any) -> None:
    if not kwargs:
        return
    conn = _get_conn()
    # Flatten current_location to current_lat/current_lng
    loc = kwargs.pop("current_location", None)
    if isinstance(loc, dict):
        kwargs["current_lat"] = float(loc.get("lat") or 19.2183)
        kwargs["current_lng"] = float(loc.get("lng") or 72.9781)
    for k, v in list(kwargs.items()):
        if k in ("stops", "schedule") and isinstance(v, list):
            kwargs[k] = json.dumps(v)
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [bus_id]
    conn.execute(f"UPDATE buses SET {cols} WHERE id = ?", vals)
    conn.commit()


def delete_bus(bus_id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM buses WHERE id = ?", (bus_id,))
    conn.commit()


# --- Conductors ---
def upsert_conductor(conductor_id: str, password: str, bus_id: str) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO conductors (conductor_id, password, bus_id) VALUES (?, ?, ?)",
        (conductor_id, password, bus_id),
    )
    conn.commit()


def get_conductor(conductor_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM conductors WHERE conductor_id = ?", (conductor_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


# --- Cameras ---
def upsert_camera(camera_id: str, password: str, bus_id: str, stream_active: int = 0) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO cameras (camera_id, password, bus_id, stream_active) VALUES (?, ?, ?, ?)",
        (camera_id, password, bus_id, stream_active),
    )
    conn.commit()


def get_camera(camera_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM cameras WHERE camera_id = ?", (camera_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_camera(camera_id: str, **kwargs: Any) -> None:
    if not kwargs:
        return
    conn = _get_conn()
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [camera_id]
    conn.execute(f"UPDATE cameras SET {cols} WHERE camera_id = ?", vals)
    conn.commit()


# --- Tap logs ---
def create_tap_log(
    user_id: str,
    bus_id: str,
    timestamp: str,
    action: str,
    from_stop: str = "",
    to_stop: str = "",
    fare_deducted: float = 0,
    payment_method: str = "",
) -> None:
    conn = _get_conn()
    conn.execute(
        """INSERT INTO tap_logs (user_id, bus_id, timestamp, action, from_stop, to_stop, fare_deducted, payment_method)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, bus_id, timestamp, action, from_stop, to_stop, fare_deducted, payment_method),
    )
    conn.commit()


def list_tap_logs() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM tap_logs ORDER BY timestamp DESC"
    ).fetchall()
    return [_tap_row_to_dict(r) for r in rows]


def list_tap_logs_for_user(user_id: str) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM tap_logs WHERE user_id = ? ORDER BY timestamp DESC",
        (str(user_id),),
    ).fetchall()
    return [_tap_row_to_dict(r) for r in rows]


def list_tap_logs_for_bus(bus_id: str, date_prefix: str = "") -> list[dict]:
    conn = _get_conn()
    if date_prefix:
        rows = conn.execute(
            "SELECT * FROM tap_logs WHERE bus_id = ? AND timestamp LIKE ? ORDER BY timestamp DESC",
            (bus_id, f"{date_prefix}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tap_logs WHERE bus_id = ? ORDER BY timestamp DESC",
            (bus_id,),
        ).fetchall()
    return [_tap_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


def _bus_row_to_dict(row: sqlite3.Row) -> Optional[dict]:
    if not row:
        return None
    d = dict(row)
    for col in ("stops", "schedule"):
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except json.JSONDecodeError:
                d[col] = []
    if "current_lat" in d and "current_lng" in d:
        d["current_location"] = {"lat": d["current_lat"], "lng": d["current_lng"]}
    return d


def _tap_row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["data"] = {
        "user_id": d.get("user_id"),
        "bus_id": d.get("bus_id"),
        "timestamp": d.get("timestamp"),
        "action": d.get("action"),
        "from_stop": d.get("from_stop"),
        "to_stop": d.get("to_stop"),
        "fare_deducted": d.get("fare_deducted"),
        "payment_method": d.get("payment_method"),
    }
    return d
