"""Insert a few clearly fictional facility and service records.

Safe to run more than once: it skips rows that already exist.
It never deletes existing data.
"""

from database import init_schema, transaction, utc_now

# Names include "Demo" so nobody confuses these with real clinics.
DEMO_FACILITIES = [
    {
        "name": "Demo PHC Rampur",
        "name_mr": "डेमो प्राथमिक आरोग्य केंद्र रामपूर",
        "facility_type": "phc",
        "village": "Rampur (fictional)",
        "taluka": "Demo Taluka",
        "district": "Demo District",
        "phone": "000-000-1001",
        "services": [
            {
                "name": "General OPD (demo)",
                "name_mr": "सामान्य ओपीडी (डेमो)",
                "description": "Fictional outpatient clinic hours for the prototype.",
            },
            {
                "name": "Antenatal care (demo)",
                "name_mr": "गर्भवती तपासणी (डेमो)",
                "description": "Fictional antenatal check-up service.",
            },
        ],
    },
    {
        "name": "Demo Sub-Centre Wadi",
        "name_mr": "डेमो उपकेंद्र वाडी",
        "facility_type": "sub_centre",
        "village": "Wadi (fictional)",
        "taluka": "Demo Taluka",
        "district": "Demo District",
        "phone": "000-000-1002",
        "services": [
            {
                "name": "Immunization (demo)",
                "name_mr": "लसीकरण (डेमो)",
                "description": "Fictional immunization session.",
            }
        ],
    },
    {
        "name": "Demo Rural Hospital Talegaon",
        "name_mr": "डेमो ग्रामीण रुग्णालय तळेगाव",
        "facility_type": "rural_hospital",
        "village": "Talegaon (fictional)",
        "taluka": "Demo Taluka",
        "district": "Demo District",
        "phone": "000-000-1003",
        "services": [
            {
                "name": "Emergency care (demo)",
                "name_mr": "आपत्कालीन सेवा (डेमो)",
                "description": "Fictional emergency desk for referrals.",
            },
            {
                "name": "Basic laboratory (demo)",
                "name_mr": "मूलभूत प्रयोगशाळा (डेमो)",
                "description": "Fictional lab tests for the prototype.",
            },
        ],
    },
]


def seed(db_path=None) -> None:
    init_schema(db_path)
    created_at = utc_now()

    with transaction(db_path) as connection:
        for facility in DEMO_FACILITIES:
            existing = connection.execute(
                "SELECT id FROM facilities WHERE name = ?",
                (facility["name"],),
            ).fetchone()

            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO facilities (
                        name, name_mr, facility_type, village, taluka, district, phone, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        facility["name"],
                        facility["name_mr"],
                        facility["facility_type"],
                        facility["village"],
                        facility["taluka"],
                        facility["district"],
                        facility["phone"],
                        created_at,
                    ),
                )
                facility_id = cursor.lastrowid
            else:
                facility_id = existing["id"]

            for service in facility["services"]:
                already_there = connection.execute(
                    """
                    SELECT id FROM services
                    WHERE facility_id = ? AND name = ?
                    """,
                    (facility_id, service["name"]),
                ).fetchone()
                if already_there is not None:
                    continue
                connection.execute(
                    """
                    INSERT INTO services (
                        facility_id, name, name_mr, description, is_available, created_at
                    ) VALUES (?, ?, ?, ?, 1, ?)
                    """,
                    (
                        facility_id,
                        service["name"],
                        service["name_mr"],
                        service["description"],
                        created_at,
                    ),
                )


if __name__ == "__main__":
    seed()
    print("Seed complete. Fictional demo facilities and services are ready.")
