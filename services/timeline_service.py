import sqlite3
from typing import Any

from database.connection import database_transaction
from database.repositories.timeline_repository import (
    create_timeline_event,
    fetch_case_timeline,
    timeline_event_exists,
)
from database.schema import initialize_database
from utils.logger import get_logger


logger = get_logger(__name__)

EVENT_CHILD_REGISTERED = "child_registered"
EVENT_ADDITIONAL_PHOTO_UPLOADED = "additional_photo_uploaded"
EVENT_FOUND_REPORT_SUBMITTED = "found_report_submitted"
EVENT_AI_MATCH_GENERATED = "ai_match_generated"
EVENT_PARENT_NOTIFIED = "parent_notified"
EVENT_AUTHORITY_VERIFIED = "authority_verified"
EVENT_CHILD_RECOVERED = "child_recovered"
EVENT_CASE_CLOSED = "case_closed"


def record_case_timeline_event(
    connection: sqlite3.Connection,
    *,
    child_id: int,
    case_id: str,
    event_type: str,
    event_title: str,
    event_description: str | None = None,
    report_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    deduplicate: bool = True,
) -> int | None:
    if deduplicate and timeline_event_exists(
        connection,
        child_id=child_id,
        event_type=event_type,
        report_id=report_id,
    ):
        return None

    event_id = create_timeline_event(
        connection,
        {
            "child_id": int(child_id),
            "case_id": case_id,
            "report_id": report_id,
            "event_type": event_type,
            "event_title": event_title,
            "event_description": event_description,
            "metadata": metadata or {},
        },
    )
    logger.info(
        "Timeline event recorded child_id=%s case_id=%s event_type=%s report_id=%s",
        child_id,
        case_id,
        event_type,
        report_id,
    )
    return event_id


def get_case_timeline(child_id: int) -> list[dict[str, Any]]:
    initialize_database()
    with database_transaction() as connection:
        return fetch_case_timeline(connection, int(child_id))
