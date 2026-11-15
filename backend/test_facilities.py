"""Tests for public facility directory queries.

Run from the backend folder:
    .\\.venv\\Scripts\\python.exe test_facilities.py
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from facilities import get_facility, list_districts, list_facilities
from seed import seed


class FacilityDirectoryTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = Path(handle.name)
        seed(self.db_path)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def test_lists_seeded_facilities_with_services(self):
        facilities = list_facilities(db_path=self.db_path)
        self.assertEqual(len(facilities), 3)
        names = {item["name"] for item in facilities}
        self.assertIn("Demo PHC Rampur", names)
        rampur = next(item for item in facilities if item["name"] == "Demo PHC Rampur")
        self.assertEqual(rampur["district"], "Demo District")
        self.assertIn("Rampur (fictional)", rampur["address"])
        self.assertTrue(rampur["services"])
        self.assertEqual(rampur["services"][0]["status"], "available")

    def test_filters_by_type_search_and_service_name(self):
        phcs = list_facilities(facility_type="phc", db_path=self.db_path)
        self.assertEqual(len(phcs), 1)
        self.assertEqual(phcs[0]["name"], "Demo PHC Rampur")

        by_name = list_facilities(q="Wadi", db_path=self.db_path)
        self.assertEqual(len(by_name), 1)
        self.assertEqual(by_name[0]["facility_type"], "sub_centre")

        by_service = list_facilities(service="Immunization", db_path=self.db_path)
        self.assertEqual(len(by_service), 1)
        self.assertEqual(by_service[0]["name"], "Demo Sub-Centre Wadi")

        by_district = list_facilities(district="Demo District", db_path=self.db_path)
        self.assertEqual(len(by_district), 3)

        missing = list_facilities(q="not-a-real-clinic", db_path=self.db_path)
        self.assertEqual(missing, [])

    def test_get_facility_details_and_missing_id(self):
        listed = list_facilities(db_path=self.db_path)
        details = get_facility(listed[0]["id"], db_path=self.db_path)
        self.assertIsNotNone(details)
        self.assertEqual(details["id"], listed[0]["id"])
        self.assertTrue(details["services"])
        self.assertIsNone(get_facility(99999, db_path=self.db_path))

    def test_districts_come_from_the_database(self):
        self.assertEqual(list_districts(db_path=self.db_path), ["Demo District"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
