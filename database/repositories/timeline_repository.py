import json
import sqlite3
from typing import Any


def create_timeline_event(connection: sqlite3.Connection, event_data: dict[str, Any]) -> int:
    metadata = event_data.get("metadata")
    metadata_json = json.dumps(metadata, sort_keys=True) if metadata else None
    cursor = connection.execute(
        """
        INSERT INTO case_timeline_events (
            child_id,
            report_id,
            case_id,
            event_type,
            event_title,
            event_description,
            metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(event_data["child_id"]),
            event_data.get("report_id"),
            event_data["case_id"],
            event_data["event_type"],
            event_data["event_title"],
            event_data.get("event_description"),
            metadata_json,
        ),
    )
    return int(cursor.lastrowid)


def fetch_case_timeline(connection: sqlite3.Connection, child_id: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            id AS timeline_event_id,
            child_id,
            report_id,
            case_id,
            event_type,
            event_title,
            event_description,
            metadata,
            created_at
        FROM case_timeline_events
        WHERE child_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (int(child_id),),
    ).fetchall()
    return [_row_to_timeline_event(row) for row in rows]


def timeline_event_exists(
    connection: sqlite3.Connection,
    *,
    child_id: int,
    event_type: str,
    report_id: int | None = None,
) -> bool:
    if report_id is None:
        row = connection.execute(
            """
            SELECT 1
            FROM case_timeline_events
            WHERE child_id = ?
              AND event_type = ?
              AND report_id IS NULL
            LIMIT 1
            """,
            (int(child_id), event_type),
        ).fetchone()
    else:
        row = connection.execute(
            """
            SELECT 1
            FROM case_timeline_events
            WHERE child_id = ?
              AND event_type = ?
              AND report_id = ?
            LIMIT 1
            """,
            (int(child_id), event_type, int(report_id)),
        ).fetchone()
    return row is not None


def _row_to_timeline_event(row: sqlite3.Row) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except json.JSONDecodeError:
            metadata = {}
    return {
        "timeline_event_id": row["timeline_event_id"],
        "child_id": row["child_id"],
        "report_id": row["report_id"],
        "case_id": row["case_id"],
        "event_type": row["event_type"],
        "event_title": row["event_title"],
        "event_description": row["event_description"],
        "metadata": metadata,
        "created_at": row["created_at"],
    }
