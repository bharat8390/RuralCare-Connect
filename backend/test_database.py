"""Readiness checks for the SQLite schema.

Run from the backend folder:
    .\\.venv\\Scripts\\python.exe test_database.py
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import REQUIRED_TABLES, init_schema, list_tables, transaction, utc_now
from seed import seed


class DatabaseReadinessTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def test_schema_can_be_initialized_and_queried(self):
        init_schema(self.db_path)
        tables = set(list_tables(self.db_path))
        self.assertTrue(set(REQUIRED_TABLES).issubset(tables))

        init_schema(self.db_path)  # running again must not wipe data or fail
        with transaction(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO facilities (
                    name, facility_type, village, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                ("Keep-Me PHC", "phc", "Test Village", utc_now()),
            )

        init_schema(self.db_path)
        with transaction(self.db_path) as connection:
            row = connection.execute(
                "SELECT name FROM facilities WHERE name = ?",
                ("Keep-Me PHC",),
            ).fetchone()
        self.assertIsNotNone(row)

    def test_unique_email_and_quantity_and_status_rules(self):
        init_schema(self.db_path)
        created_at = utc_now()

        with transaction(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO facilities (name, facility_type, village, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("Rule Check PHC", "phc", "Test Village", created_at),
            )
            facility_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO users (full_name, email, role, facility_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("Demo ASHA", "asha.demo@example.invalid", "asha", facility_id, created_at, created_at),
            )

        with self.assertRaises(sqlite3.IntegrityError):
            with transaction(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO users (full_name, email, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("Copy", "asha.demo@example.invalid", "admin", created_at, created_at),
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with transaction(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO resource_status (
                        facility_id, resource_name, quantity, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (facility_id, "Oxygen cylinders (demo)", -1, "available", created_at),
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with transaction(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO resource_status (
                        facility_id, resource_name, quantity, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (facility_id, "Beds (demo)", 2, "unknown", created_at),
                )

    def test_foreign_keys_are_enforced(self):
        init_schema(self.db_path)
        with transaction(self.db_path) as connection:
            enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(enabled, 1)

        with self.assertRaises(sqlite3.IntegrityError):
            with transaction(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO services (facility_id, name, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (999, "Service for a missing facility", utc_now()),
                )

    def test_seed_is_idempotent(self):
        seed(self.db_path)
        seed(self.db_path)
        with transaction(self.db_path) as connection:
            facility_count = connection.execute(
                "SELECT COUNT(*) AS n FROM facilities"
            ).fetchone()["n"]
            service_count = connection.execute(
                "SELECT COUNT(*) AS n FROM services"
            ).fetchone()["n"]
        self.assertEqual(facility_count, 3)
        self.assertEqual(service_count, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
