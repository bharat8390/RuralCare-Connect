
"""SQLite operations for RuralCare Connect referrals."""

import sqlite3

from database import get_connection, utc_now


ALLOWED_STATUSES = {"pending", "accepted", "completed", "cancelled"}

STATUS_TRANSITIONS = {
    "pending": {"accepted", "cancelled"},
    "accepted": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def _referral_dict(row):
    if row is None:
        return None

    return dict(row)


def list_referrals(status=None, db_path=None):
    connection = get_connection(db_path)
    try:
        sql = """
            SELECT r.*,
                   source.name AS from_facility_name,
                   destination.name AS to_facility_name,
                   s.name AS service_name
            FROM referrals r
            JOIN facilities source ON source.id = r.from_facility_id
            JOIN facilities destination ON destination.id = r.to_facility_id
            LEFT JOIN services s ON s.id = r.service_id
        """
        params = []

        if status:
            if status not in ALLOWED_STATUSES:
                raise ValueError("Unknown referral status.")
            sql += " WHERE r.status = ?"
            params.append(status)

        sql += " ORDER BY r.created_at DESC, r.id DESC"

        rows = connection.execute(sql, params).fetchall()
        return [_referral_dict(row) for row in rows]
    finally:
        connection.close()


def get_referral(referral_id, db_path=None):
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            """
            SELECT r.*,
                   source.name AS from_facility_name,
                   destination.name AS to_facility_name,
                   s.name AS service_name
            FROM referrals r
            JOIN facilities source ON source.id = r.from_facility_id
            JOIN facilities destination ON destination.id = r.to_facility_id
            LEFT JOIN services s ON s.id = r.service_id
            WHERE r.id = ?
            """,
            (referral_id,),
        ).fetchone()
        return _referral_dict(row)
    finally:
        connection.close()


def create_referral(
    *,
    patient_name,
    patient_age,
    from_facility_id,
    to_facility_id,
    service_id=None,
    referred_by_user_id=None,
    notes=None,
    db_path=None,
):
    name = patient_name.strip()
    if not name:
        raise ValueError("Patient name is required.")

    if from_facility_id == to_facility_id:
        raise ValueError("Source and destination facilities must differ.")

    connection = get_connection(db_path)
    try:
        source = connection.execute(
            "SELECT id FROM facilities WHERE id = ?",
            (from_facility_id,),
        ).fetchone()
        destination = connection.execute(
            "SELECT id FROM facilities WHERE id = ?",
            (to_facility_id,),
        ).fetchone()

        if source is None or destination is None:
            raise ValueError("Source or destination facility was not found.")

        if service_id is not None:
            service = connection.execute(
                """
                SELECT id FROM services
                WHERE id = ? AND facility_id = ?
                """,
                (service_id, to_facility_id),
            ).fetchone()
            if service is None:
                raise ValueError(
                    "The selected service must belong to the destination facility."
                )

        now = utc_now()
        cursor = connection.execute(
            """
            INSERT INTO referrals (
                patient_name, patient_age, from_facility_id,
                to_facility_id, service_id, referred_by_user_id,
                status, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                name,
                patient_age,
                from_facility_id,
                to_facility_id,
                service_id,
                referred_by_user_id,
                notes.strip() if notes else None,
                now,
                now,
            ),
        )
        referral_id = cursor.lastrowid
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.rollback()
        raise ValueError(
            "Referral contains an invalid user, facility, or service reference."
        ) from exc
    finally:
        connection.close()

    return get_referral(referral_id, db_path=db_path)


def update_referral_status(referral_id, new_status, db_path=None):
    if new_status not in ALLOWED_STATUSES:
        raise ValueError("Unknown referral status.")

    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT status FROM referrals WHERE id = ?",
            (referral_id,),
        ).fetchone()

        if row is None:
            return None

        current_status = row["status"]
        if new_status not in STATUS_TRANSITIONS[current_status]:
            raise ValueError(
                f"Cannot change referral status from {current_status} to {new_status}."
            )

        connection.execute(
            """
            UPDATE referrals
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_status, utc_now(), referral_id),
        )
        connection.commit()
    finally:
        connection.close()

    return get_referral(referral_id, db_path=db_path)
