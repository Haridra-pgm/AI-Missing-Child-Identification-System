import json
import math
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from config.settings import (
    NOMINATIM_COUNTRY_CODES,
    NOMINATIM_MIN_REQUEST_INTERVAL_SECONDS,
    NOMINATIM_SEARCH_URL,
    NOMINATIM_TIMEOUT_SECONDS,
    NOMINATIM_USER_AGENT,
    OVERPASS_API_URL,
    OVERPASS_TIMEOUT_SECONDS,
    POLICE_SEARCH_RADIUS_METERS,
    POLICE_STATION_RESULT_LIMIT,
)
from database.connection import database_transaction
from database.repositories.location_repository import (
    fetch_cached_geocode,
    fetch_cached_police_stations,
    upsert_geocode_cache,
    upsert_police_station_cache,
)
from database.schema import initialize_database
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)

_nominatim_lock = threading.Lock()
_last_nominatim_request_at = 0.0


class LocationLookupError(Exception):
    """Raised when a location lookup cannot be completed."""


def geocode_required_location(location: str, *, field_name: str) -> dict[str, Any]:
    normalized_query = _normalize_location_query(location)
    if not normalized_query:
        raise ValidationError(f"{field_name} is required.")

    try:
        result = geocode_location(normalized_query)
    except LocationLookupError as exc:
        logger.info("Geocoding failed field=%s query=%s error=%s", field_name, normalized_query, exc)
        raise ValidationError(
            f"{field_name} could not be located on the map. Please enter a more specific place, "
            "such as area, landmark, city, and state."
        ) from exc

    return result


def geocode_location(location: str) -> dict[str, Any]:
    query = _normalize_location_query(location)
    if not query:
        raise LocationLookupError("Location query is empty.")

    initialize_database()
    with database_transaction() as connection:
        cached = fetch_cached_geocode(connection, query)
    if cached is not None:
        logger.info("Geocoding cache hit query=%s", query)
        return cached

    result = _request_nominatim_geocode(query)
    initialize_database()
    with database_transaction() as connection:
        upsert_geocode_cache(
            connection,
            query=query,
            display_name=result["display_name"],
            latitude=result["latitude"],
            longitude=result["longitude"],
        )
    logger.info("Geocoding cache stored query=%s latitude=%s longitude=%s", query, result["latitude"], result["longitude"])
    return result


def find_nearby_police_stations(
    latitude: float,
    longitude: float,
    *,
    radius_meters: int = POLICE_SEARCH_RADIUS_METERS,
    limit: int = POLICE_STATION_RESULT_LIMIT,
) -> list[dict[str, Any]]:
    lat = _normalize_coordinate(latitude, "Latitude", -90.0, 90.0)
    lon = _normalize_coordinate(longitude, "Longitude", -180.0, 180.0)
    radius = max(int(radius_meters), 500)
    cache_key = f"{round(lat, 4)}:{round(lon, 4)}:{radius}"

    initialize_database()
    with database_transaction() as connection:
        cached_json = fetch_cached_police_stations(connection, cache_key)
    if cached_json:
        try:
            cached_results = json.loads(cached_json)
            return cached_results[:limit]
        except json.JSONDecodeError:
            logger.warning("Ignoring malformed police station cache cache_key=%s", cache_key)

    stations = _request_overpass_police_stations(lat, lon, radius, limit)
    initialize_database()
    with database_transaction() as connection:
        upsert_police_station_cache(
            connection,
            cache_key=cache_key,
            latitude=lat,
            longitude=lon,
            radius_meters=radius,
            response_json=json.dumps(stations, sort_keys=True),
        )
    return stations[:limit]


def _request_nominatim_geocode(query: str) -> dict[str, Any]:
    parameters = {
        "q": query,
        "format": "jsonv2",
        "limit": "1",
        "addressdetails": "1",
    }
    if NOMINATIM_COUNTRY_CODES:
        parameters["countrycodes"] = NOMINATIM_COUNTRY_CODES

    url = f"{NOMINATIM_SEARCH_URL}?{urllib.parse.urlencode(parameters)}"
    payload = _http_get_json(url, timeout=NOMINATIM_TIMEOUT_SECONDS, rate_limit_nominatim=True)
    if not isinstance(payload, list) or not payload:
        raise LocationLookupError("No geocoding result found.")

    first_result = payload[0]
    try:
        latitude = round(float(first_result["lat"]), 6)
        longitude = round(float(first_result["lon"]), 6)
    except (KeyError, TypeError, ValueError) as exc:
        raise LocationLookupError("Geocoding response did not include valid coordinates.") from exc

    display_name = str(first_result.get("display_name") or query)
    return {
        "query": query,
        "display_name": display_name,
        "latitude": latitude,
        "longitude": longitude,
        "provider": "nominatim",
    }


def _request_overpass_police_stations(
    latitude: float,
    longitude: float,
    radius_meters: int,
    limit: int,
) -> list[dict[str, Any]]:
    query = f"""
    [out:json][timeout:{max(10, int(OVERPASS_TIMEOUT_SECONDS) - 2)}];
    (
      node["amenity"="police"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="police"](around:{radius_meters},{latitude},{longitude});
      relation["amenity"="police"](around:{radius_meters},{latitude},{longitude});
    );
    out center tags;
    """
    request_data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        OVERPASS_API_URL,
        data=request_data,
        headers={
            "User-Agent": NOMINATIM_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=OVERPASS_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Overpass police station lookup failed: %s", exc)
        return []

    stations = []
    for element in payload.get("elements", []):
        station = _overpass_element_to_station(element, latitude, longitude)
        if station is not None:
            stations.append(station)

    stations.sort(key=lambda item: item["distance_km"])
    return stations[:limit]


def _overpass_element_to_station(element: dict[str, Any], source_lat: float, source_lon: float) -> dict[str, Any] | None:
    tags = element.get("tags") or {}
    lat = element.get("lat") or (element.get("center") or {}).get("lat")
    lon = element.get("lon") or (element.get("center") or {}).get("lon")
    if lat is None or lon is None:
        return None
    try:
        station_lat = float(lat)
        station_lon = float(lon)
    except (TypeError, ValueError):
        return None

    name = str(tags.get("name") or "Police Station")
    address = _format_osm_address(tags)
    distance_km = round(_haversine_km(source_lat, source_lon, station_lat, station_lon), 2)
    return {
        "name": name,
        "address": address,
        "distance_km": distance_km,
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "latitude": round(station_lat, 6),
        "longitude": round(station_lon, 6),
        "navigation_link": (
            "https://www.openstreetmap.org/directions?engine=fossgis_osrm_car"
            f"&route={source_lat}%2C{source_lon}%3B{station_lat}%2C{station_lon}"
        ),
    }


def _format_osm_address(tags: dict[str, Any]) -> str:
    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:state"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(str(part) for part in address_parts if part)
    return address or str(tags.get("addr:full") or tags.get("description") or "Address not available")


def _http_get_json(url: str, *, timeout: int, rate_limit_nominatim: bool = False) -> Any:
    if rate_limit_nominatim:
        _respect_nominatim_rate_limit()
    request = urllib.request.Request(url, headers={"User-Agent": NOMINATIM_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LocationLookupError("Location provider request failed.") from exc


def _respect_nominatim_rate_limit() -> None:
    global _last_nominatim_request_at
    with _nominatim_lock:
        elapsed = time.monotonic() - _last_nominatim_request_at
        if elapsed < NOMINATIM_MIN_REQUEST_INTERVAL_SECONDS:
            time.sleep(NOMINATIM_MIN_REQUEST_INTERVAL_SECONDS - elapsed)
        _last_nominatim_request_at = time.monotonic()


def _normalize_location_query(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalize_coordinate(value: Any, field_name: str, minimum: float, maximum: float) -> float:
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number.") from exc
    if coordinate < minimum or coordinate > maximum:
        raise ValidationError(f"{field_name} must be between {minimum:g} and {maximum:g}.")
    return round(coordinate, 6)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius_km * c
