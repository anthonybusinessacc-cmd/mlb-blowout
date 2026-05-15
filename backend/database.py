import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "blowout.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            threshold INTEGER DEFAULT 5,
            phone_number TEXT DEFAULT '',
            sms_enabled INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            game_pk TEXT,
            message TEXT,
            sent_at TEXT
        )
    """)
    # Insert default settings row if none exists
    cur.execute("SELECT COUNT(*) FROM settings")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute(
            "INSERT INTO settings (threshold, phone_number, sms_enabled) VALUES (5, '', 1)"
        )
    conn.commit()
    conn.close()


def get_settings() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT threshold, phone_number, sms_enabled FROM settings WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row is None:
        return {"threshold": 5, "phone_number": "", "sms_enabled": True}
    return {
        "threshold": row["threshold"],
        "phone_number": row["phone_number"],
        "sms_enabled": bool(row["sms_enabled"]),
    }


def update_settings(data: dict):
    if not data:
        return
    conn = get_conn()
    cur = conn.cursor()
    allowed = {"threshold", "phone_number", "sms_enabled"}
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        conn.close()
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values())
    cur.execute(f"UPDATE settings SET {set_clause} WHERE id = 1", values)
    conn.commit()
    conn.close()


def add_notification(game_pk: str, message: str):
    conn = get_conn()
    cur = conn.cursor()
    sent_at = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO notifications (game_pk, message, sent_at) VALUES (?, ?, ?)",
        (str(game_pk), message, sent_at),
    )
    conn.commit()
    conn.close()


def get_today_notifications() -> list:
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur.execute(
        "SELECT game_pk, message, sent_at FROM notifications WHERE sent_at LIKE ? ORDER BY sent_at DESC",
        (f"{today}%",),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def has_notified(game_pk: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur.execute(
        "SELECT COUNT(*) FROM notifications WHERE game_pk = ? AND sent_at LIKE ?",
        (str(game_pk), f"{today}%"),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0
