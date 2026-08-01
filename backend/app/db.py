"""SQLite persistence: user accounts, login sessions, and prediction history.

A single SQLite file (dashboard.db) is used — no separate database server is
needed. This keeps the project's original "no database" simplicity mostly
intact while adding just enough storage for login and for predictions to
survive a page refresh.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "dashboard.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS prediction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    machine_category TEXT NOT NULL,
    engine_rpm REAL NOT NULL,
    lub_oil_pressure REAL NOT NULL,
    lub_oil_temperature REAL NOT NULL,
    coolant_temperature REAL NOT NULL,
    exhaust_temperature REAL,
    status TEXT NOT NULL,
    fault_probability REAL NOT NULL,
    fault_types TEXT NOT NULL,
    model_used TEXT NOT NULL,
    reading_timestamp TEXT
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


# --- Users ---------------------------------------------------------------

def get_user_by_username(username: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str, salt: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt),
        )


def count_users() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


# --- Sessions --------------------------------------------------------------

def create_session(token: str, user_id: int, created_at: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, created_at),
        )


def get_session(token: str):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT sessions.token, sessions.created_at, users.id AS user_id, users.username
            FROM sessions JOIN users ON sessions.user_id = users.id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        return dict(row) if row else None


def delete_session(token: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# --- Prediction history ------------------------------------------------------

def insert_history_row(row: dict, created_at: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO prediction_history (
                created_at, machine_id, machine_category, engine_rpm,
                lub_oil_pressure, lub_oil_temperature, coolant_temperature,
                exhaust_temperature, status, fault_probability, fault_types,
                model_used, reading_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                row["machine_id"],
                row["machine_category"],
                row["engine_rpm"],
                row["lub_oil_pressure"],
                row["lub_oil_temperature"],
                row["coolant_temperature"],
                row["exhaust_temperature"],
                row["status"],
                row["fault_probability"],
                json.dumps(row["fault_types"]),
                row["model_used"],
                row["timestamp"],
            ),
        )
        return cursor.lastrowid


def get_history_rows(limit: int = 500):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM prediction_history ORDER BY id ASC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "row_index": r["id"],  # kept for schema compatibility; id is now the real ordering key
                "machine_id": r["machine_id"],
                "machine_category": r["machine_category"],
                "engine_rpm": r["engine_rpm"],
                "lub_oil_pressure": r["lub_oil_pressure"],
                "lub_oil_temperature": r["lub_oil_temperature"],
                "coolant_temperature": r["coolant_temperature"],
                "exhaust_temperature": r["exhaust_temperature"],
                "status": r["status"],
                "fault_probability": r["fault_probability"],
                "fault_types": json.loads(r["fault_types"]),
                "model_used": r["model_used"],
                "timestamp": r["reading_timestamp"],
            }
            for r in rows
        ]


def clear_history_rows():
    with get_connection() as conn:
        conn.execute("DELETE FROM prediction_history")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'prediction_history'")
