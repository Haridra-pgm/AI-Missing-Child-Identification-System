import sqlite3
from datetime import datetime, timedelta
from typing import Any


def fetch_cached_geocode(connection: sqlite3.Connection, query: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            query,
            display_name,
            latitude,
            longitude,
            provider,
            created_at,
            updated_at
        FROM geocoding_cache
        WHERE query = ?
        LIMIT 1
        """,
        (query,),
    ).fetchone()
    if row is None:
        return None
    return {
        "query": row["query"],
        "display_name": row["display_name"],
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "provider": row["provider"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def upsert_geocode_cache(
    connection: sqlite3.Connection,
    *,
    query: str,
    display_name: str,
    latitude: float,
    longitude: float,
    provider: str = "nominatim",
) -> None:
    connection.execute(
        """
        INSERT INTO geocoding_cache (
            query,
            display_name,
            latitude,
            longitude,
            provider
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(query) DO UPDATE SET
            display_name = excluded.display_name,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            provider = excluded.provider,
            updated_at = CURRENT_TIMESTAMP
        """,
        (query, display_name, latitude, longitude, provider),
    )


def fetch_cached_police_stations(
    connection: sqlite3.Connection,
    cache_key: str,
    *,
    max_age_hours: int = 24,
) -> str | None:
    row = connection.execute(
        """
        SELECT response_json, updated_at
        FROM police_station_cache
        WHERE cache_key = ?
        LIMIT 1
        """,
        (cache_key,),
    ).fetchone()
    if row is None:
        return None

    updated_at = _parse_timestamp(row["updated_at"])
    if updated_at is not None and datetime.utcnow() - updated_at > timedelta(hours=max_age_hours):
        return None
    return str(row["response_json"])


def upsert_police_station_cache(
    connection: sqlite3.Connection,
    *,
    cache_key: str,
    latitude: float,
    longitude: float,
    radius_meters: int,
    response_json: str,
) -> None:
    connection.execute(
        """
        INSERT INTO police_station_cache (
            cache_key,
            latitude,
            longitude,
            radius_meters,
            response_json
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            radius_meters = excluded.radius_meters,
            response_json = excluded.response_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (cache_key, latitude, longitude, radius_meters, response_json),
    )


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None
