
from datetime import datetime, timezone

from database import get_connection, utc_now


ALLOWED_FOLLOW_UP_STATUSES = {"scheduled", "completed", "missed"}


def list_follow_ups(status=None):
    """Return follow-ups with their linked referral details."""
    connection = get_connection()

    try:
        query = """
            SELECT
                fu.id,
                fu.referral_id,
                fu.assigned_to_user_id,
                fu.due_at,
                fu.status,
                fu.notes,
                fu.created_at,
                fu.completed_at,
                r.patient_name,
                r.from_facility_id,
                r.to_facility_id
            FROM follow_ups fu
            JOIN referrals r ON r.id = fu.referral_id
        """
        params = ()

        if status is not None:
            if status not in ALLOWED_FOLLOW_UP_STATUSES:
                raise ValueError("Invalid follow-up status.")
            query += " WHERE fu.status = ?"
            params = (status,)

        query += " ORDER BY fu.due_at ASC"

        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def create_follow_up(
    referral_id,
    due_at,
    notes=None,
    assigned_to_user_id=None,
):
    """Schedule a follow-up for an existing referral."""
    connection = get_connection()

    try:
        referral = connection.execute(
            "SELECT id FROM referrals WHERE id = ?",
            (referral_id,),
        ).fetchone()

        if referral is None:
            raise ValueError("Referral not found.")

        try:
            parsed_due_at = datetime.fromisoformat(
                due_at.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            raise ValueError(
                "due_at must be a valid ISO 8601 date and time."
            ) from None

        if parsed_due_at.tzinfo is None:
            raise ValueError(
                "due_at must include a timezone, such as +05:30 or Z."
            )

        if parsed_due_at <= datetime.now(timezone.utc):
            raise ValueError("Follow-up due date must be in the future.")

        if assigned_to_user_id is not None:
            user = connection.execute(
                "SELECT id FROM users WHERE id = ?",
                (assigned_to_user_id,),
            ).fetchone()

            if user is None:
                raise ValueError("Assigned user not found.")

        cursor = connection.execute(
            """
            INSERT INTO follow_ups (
                referral_id,
                assigned_to_user_id,
                due_at,
                status,
                notes,
                created_at
            )
            VALUES (?, ?, ?, 'scheduled', ?, ?)
            """,
            (
                referral_id,
                assigned_to_user_id,
                parsed_due_at.isoformat(),
                notes,
                utc_now(),
            ),
        )
        connection.commit()

        return connection.execute(
            """
            SELECT *
            FROM follow_ups
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_follow_up_status(follow_up_id, status):
    """Mark a scheduled follow-up as completed or missed."""
    if status not in {"completed", "missed"}:
        raise ValueError(
            "Status must be completed or missed."
        )

    connection = get_connection()

    try:
        follow_up = connection.execute(
            "SELECT * FROM follow_ups WHERE id = ?",
            (follow_up_id,),
        ).fetchone()

        if follow_up is None:
            raise ValueError("Follow-up not found.")

        if follow_up["status"] != "scheduled":
            raise ValueError(
                "Only scheduled follow-ups can be updated."
            )

        completed_at = utc_now() if status == "completed" else None

        connection.execute(
            """
            UPDATE follow_ups
            SET status = ?, completed_at = ?
            WHERE id = ?
            """,
            (status, completed_at, follow_up_id),
        )
        connection.commit()

        return dict(
            connection.execute(
                "SELECT * FROM follow_ups WHERE id = ?",
                (follow_up_id,),
            ).fetchone()
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
