
from database import get_connection, utc_now

ALLOWED_RESOURCE_STATUSES = {"available", "low", "unavailable"}


def list_resources(facility_id=None):
    conn = get_connection()

    try:
        query = """
            SELECT
                r.facility_id,
                f.name AS facility_name,
                r.resource_name,
                r.quantity,
                r.status,
                r.updated_at
            FROM resource_status r
            JOIN facilities f ON f.id = r.facility_id
        """
        params = ()

        if facility_id is not None:
            query += " WHERE r.facility_id = ?"
            params = (facility_id,)

        query += " ORDER BY f.name, r.resource_name"

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def upsert_resource(facility_id, resource_name, quantity, status):
    resource_name = resource_name.strip()

    if not resource_name:
        raise ValueError("Resource name is required.")

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    if status not in ALLOWED_RESOURCE_STATUSES:
        raise ValueError("Unknown resource status.")

    conn = get_connection()

    try:
        facility = conn.execute(
            "SELECT id FROM facilities WHERE id = ?",
            (facility_id,),
        ).fetchone()

        if facility is None:
            raise ValueError("Facility not found.")

        existing = conn.execute(
            """
            SELECT facility_id
            FROM resource_status
            WHERE facility_id = ? AND resource_name = ?
            """,
            (facility_id, resource_name),
        ).fetchone()

        now = utc_now()

        if existing:
            conn.execute(
                """
                UPDATE resource_status
                SET quantity = ?, status = ?, updated_at = ?
                WHERE facility_id = ? AND resource_name = ?
                """,
                (quantity, status, now, facility_id, resource_name),
            )
        else:
            conn.execute(
                """
                INSERT INTO resource_status
                    (facility_id, resource_name, quantity, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (facility_id, resource_name, quantity, status, now),
            )

        conn.commit()

        row = conn.execute(
            """
            SELECT
                r.facility_id,
                f.name AS facility_name,
                r.resource_name,
                r.quantity,
                r.status,
                r.updated_at
            FROM resource_status r
            JOIN facilities f ON f.id = r.facility_id
            WHERE r.facility_id = ? AND r.resource_name = ?
            """,
            (facility_id, resource_name),
        ).fetchone()

        return dict(row)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_resource_summary():
    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_resources,
                SUM(CASE WHEN status = 'low' THEN 1 ELSE 0 END)
                    AS low_resources,
                SUM(CASE WHEN status = 'unavailable' THEN 1 ELSE 0 END)
                    AS unavailable_resources
            FROM resource_status
            """
        ).fetchone()

        return {
            "total_resources": row["total_resources"] or 0,
            "low_resources": row["low_resources"] or 0,
            "unavailable_resources": row["unavailable_resources"] or 0,
        }
    finally:
        conn.close()
