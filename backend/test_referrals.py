
"""Tests for RuralCare Connect referral operations."""

import tempfile
import unittest
from pathlib import Path

from database import get_connection
from referrals import (
    create_referral,
    list_referrals,
    update_referral_status,
)
from seed import seed


class ReferralTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        seed(self.db_path)
        self.addCleanup(self._cleanup)

        connection = get_connection(self.db_path)
        try:
            facilities = connection.execute(
                "SELECT id FROM facilities ORDER BY id"
            ).fetchall()
            self.source_id = facilities[0]["id"]
            self.destination_id = facilities[1]["id"]

            service = connection.execute(
                "SELECT id FROM services WHERE facility_id = ? LIMIT 1",
                (self.destination_id,),
            ).fetchone()
            self.service_id = service["id"] if service else None
        finally:
            connection.close()

    def _cleanup(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def _create(self):
        return create_referral(
            patient_name="Fictional Demo Patient",
            patient_age=35,
            from_facility_id=self.source_id,
            to_facility_id=self.destination_id,
            service_id=self.service_id,
            notes="Fictional test record only",
            db_path=self.db_path,
        )

    def test_create_and_list_referral(self):
        referral = self._create()

        self.assertIsNotNone(referral["id"])
        self.assertEqual(referral["status"], "pending")
        self.assertEqual(referral["from_facility_id"], self.source_id)
        self.assertEqual(referral["to_facility_id"], self.destination_id)

        referrals = list_referrals(db_path=self.db_path)
        self.assertEqual(len(referrals), 1)
        self.assertEqual(referrals[0]["id"], referral["id"])

    def test_status_can_progress_to_completed(self):
        referral = self._create()
        referral_id = referral["id"]

        accepted = update_referral_status(
            referral_id, "accepted", db_path=self.db_path
        )
        self.assertEqual(accepted["status"], "accepted")

        completed = update_referral_status(
            referral_id, "completed", db_path=self.db_path
        )
        self.assertEqual(completed["status"], "completed")

    def test_invalid_status_transition_is_rejected(self):
        referral = self._create()

        with self.assertRaises(ValueError):
            update_referral_status(
                referral["id"], "completed", db_path=self.db_path
            )

        unchanged = list_referrals(db_path=self.db_path)
        self.assertEqual(unchanged[0]["status"], "pending")

    def test_same_source_and_destination_is_rejected(self):
        with self.assertRaises(ValueError):
            create_referral(
                patient_name="Fictional Demo Patient",
                patient_age=35,
                from_facility_id=self.source_id,
                to_facility_id=self.source_id,
                db_path=self.db_path,
            )

    def test_missing_referral_returns_none(self):
        self.assertIsNone(
            update_referral_status(999999, "accepted", db_path=self.db_path)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

