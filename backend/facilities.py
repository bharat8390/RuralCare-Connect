"""Read public healthcare facilities from the existing SQLite database."""

from __future__ import annotations

from pathlib import Path

from database import get_connection

FACILITY_TYPES = ("sub_centre", "phc", "chc", "rural_hospital")


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _service_status(is_available: int) -> str:
    return "available" if is_available else "unavailable"


def _address(row) -> str:
    parts = [row["village"], row["taluka"], row["district"]]
    return ", ".join(part for part in parts if part)


def _facility_dict(row, services: list[dict] | None = None) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "name_mr": row["name_mr"],
        "facility_type": row["facility_type"],
        "village": row["village"],
        "taluka": row["taluka"],
        "district": row["district"],
        "phone": row["phone"],
        "address": _address(row),
        "services": services if services is not None else [],
    }


def _service_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "name_mr": row["name_mr"],
        "description": row["description"],
        "status": _service_status(row["is_available"]),
    }


def _services_for_facilities(connection, facility_ids: list[int]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {facility_id: [] for facility_id in facility_ids}
    if not facility_ids:
        return grouped

    placeholders = ",".join("?" for _ in facility_ids)
    rows = connection.execute(
        f"""
        SELECT id, facility_id, name, name_mr, description, is_available
        FROM services
        WHERE facility_id IN ({placeholders})
        ORDER BY name
        """,
        facility_ids,
    ).fetchall()
    for row in rows:
        grouped[row["facility_id"]].append(_service_dict(row))
    return grouped


def list_districts(db_path: str | Path | None = None) -> list[str]:
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            """
            SELECT DISTINCT district
            FROM facilities
            WHERE district IS NOT NULL AND TRIM(district) != ''
            ORDER BY district
            """
        ).fetchall()
        return [row["district"] for row in rows]
    finally:
        connection.close()


def list_facilities(
    q: str | None = None,
    district: str | None = None,
    facility_type: str | None = None,
    service: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Return facilities that match the optional search and filters."""
    search = _blank_to_none(q)
    district = _blank_to_none(district)
    facility_type = _blank_to_none(facility_type)
    service = _blank_to_none(service)

    clauses = ["1 = 1"]
    params: list[str] = []

    if search:
        like = f"%{search}%"
        clauses.append(
            """
            (
                f.name LIKE ?
                OR f.name_mr LIKE ?
                OR f.village LIKE ?
                OR f.taluka LIKE ?
                OR f.district LIKE ?
                OR EXISTS (
                    SELECT 1 FROM services s_search
                    WHERE s_search.facility_id = f.id
                      AND (s_search.name LIKE ? OR s_search.name_mr LIKE ?)
                )
            )
            """
        )
        params.extend([like, like, like, like, like, like, like])

    if district:
        clauses.append("f.district = ?")
        params.append(district)

    if facility_type:
        clauses.append("f.facility_type = ?")
        params.append(facility_type)

    if service:
        like = f"%{service}%"
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM services s_filter
                WHERE s_filter.facility_id = f.id
                  AND (s_filter.name LIKE ? OR s_filter.name_mr LIKE ?)
            )
            """
        )
        params.extend([like, like])

    where_sql = " AND ".join(clauses)
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            f"""
            SELECT id, name, name_mr, facility_type, village, taluka, district, phone
            FROM facilities f
            WHERE {where_sql}
            ORDER BY f.name
            """,
            params,
        ).fetchall()
        facility_ids = [row["id"] for row in rows]
        services_by_id = _services_for_facilities(connection, facility_ids)
        return [_facility_dict(row, services_by_id[row["id"]]) for row in rows]
    finally:
        connection.close()


def get_facility(facility_id: int, db_path: str | Path | None = None) -> dict | None:
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            """
            SELECT id, name, name_mr, facility_type, village, taluka, district, phone
            FROM facilities
            WHERE id = ?
            """,
            (facility_id,),
        ).fetchone()
        if row is None:
            return None
        services = _services_for_facilities(connection, [row["id"]])[row["id"]]
        return _facility_dict(row, services)
    finally:
        connection.close()
