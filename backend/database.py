"""SQLite helpers for RuralCare Connect.

Uses Python's built-in sqlite3 module (no ORM).
Schema setup only creates missing tables. It never drops tables
and never deletes existing rows.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ruralcare.db"

REQUIRED_TABLES = (
    "users",
    "facilities",
    "services",
    "referrals",
    "follow_ups",
    "resource_status",
)


def utc_now() -> str:
    """Return the current time in UTC, stored as text."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys turned on."""
    path = Path(db_path) if db_path is not None else DB_PATH
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless this pragma is set on every connection.
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def transaction(db_path: str | Path | None = None):
    """Run several SQL statements as one transaction.

    Commits if everything succeeds. Rolls back if any statement fails.
    """
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_schema(db_path: str | Path | None = None) -> None:
    """Create the six tables if they do not already exist."""
    with transaction(db_path) as connection:
        # Facilities first so other tables can point to them.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                name_mr TEXT,
                facility_type TEXT NOT NULL CHECK (
                    facility_type IN ('sub_centre', 'phc', 'chc', 'rural_hospital')
                ),
                village TEXT NOT NULL,
                taluka TEXT,
                district TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK (
                    role IN ('asha', 'phc_staff', 'admin')
                ),
                facility_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY,
                facility_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                name_mr TEXT,
                description TEXT,
                is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
                created_at TEXT NOT NULL,
                FOREIGN KEY (facility_id) REFERENCES facilities(id),
                UNIQUE (facility_id, name)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_age INTEGER,
                from_facility_id INTEGER NOT NULL,
                to_facility_id INTEGER NOT NULL,
                service_id INTEGER,
                referred_by_user_id INTEGER,
                status TEXT NOT NULL CHECK (
                    status IN ('pending', 'accepted', 'completed', 'cancelled')
                ),
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (from_facility_id) REFERENCES facilities(id),
                FOREIGN KEY (to_facility_id) REFERENCES facilities(id),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (referred_by_user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY,
                referral_id INTEGER NOT NULL,
                assigned_to_user_id INTEGER,
                due_at TEXT,
                status TEXT NOT NULL CHECK (
                    status IN ('scheduled', 'completed', 'missed')
                ),
                notes TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (referral_id) REFERENCES referrals(id),
                FOREIGN KEY (assigned_to_user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resource_status (
                id INTEGER PRIMARY KEY,
                facility_id INTEGER NOT NULL,
                resource_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                status TEXT NOT NULL CHECK (
                    status IN ('available', 'low', 'unavailable')
                ),
                updated_at TEXT NOT NULL,
                FOREIGN KEY (facility_id) REFERENCES facilities(id),
                UNIQUE (facility_id, resource_name)
            )
            """
        )


def list_tables(db_path: str | Path | None = None) -> list[str]:
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        return [row["name"] for row in rows]
    finally:
        connection.close()
