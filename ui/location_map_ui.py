from html import escape
from typing import Any

import streamlit as st


def render_location_map(
    *,
    last_seen_location: str | None,
    last_seen_latitude: Any,
    last_seen_longitude: Any,
    last_seen_timestamp: str | None,
    found_location: str | None = None,
    found_latitude: Any = None,
    found_longitude: Any = None,
    found_timestamp: str | None = None,
    key: str | None = None,
) -> None:
    map_object = build_location_map(
        last_seen_location=last_seen_location,
        last_seen_latitude=last_seen_latitude,
        last_seen_longitude=last_seen_longitude,
        last_seen_timestamp=last_seen_timestamp,
        found_location=found_location,
        found_latitude=found_latitude,
        found_longitude=found_longitude,
        found_timestamp=found_timestamp,
    )
    if map_object is None:
        st.info("Map unavailable because coordinates are not stored for this case/report.")
        return

    try:
        from streamlit_folium import st_folium
    except ImportError:
        st.warning("Install streamlit-folium to display the interactive location map.")
        return

    try:
        with st.container(border=True):
            st_folium(map_object, height=360, use_container_width=True, returned_objects=[], key=key)
    except TypeError:
        with st.container(border=True):
            st_folium(map_object, height=360, width=720, key=key)


def build_location_map(
    *,
    last_seen_location: str | None,
    last_seen_latitude: Any,
    last_seen_longitude: Any,
    last_seen_timestamp: str | None,
    found_location: str | None = None,
    found_latitude: Any = None,
    found_longitude: Any = None,
    found_timestamp: str | None = None,
) -> Any | None:
    try:
        import folium
    except ImportError:
        return None

    last_seen_point = _coordinate_pair(last_seen_latitude, last_seen_longitude)
    found_point = _coordinate_pair(found_latitude, found_longitude)
    if last_seen_point is None and found_point is None:
        return None

    points = [point for point in (last_seen_point, found_point) if point is not None]
    center = (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )
    zoom_start = 12 if len(points) > 1 else 14
    map_object = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")

    if last_seen_point is not None:
        folium.Marker(
            location=last_seen_point,
            popup=_popup_html(
                title="Last Seen Location",
                location=last_seen_location,
                latitude=last_seen_point[0],
                longitude=last_seen_point[1],
                timestamp=last_seen_timestamp,
            ),
            tooltip="Last Seen",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(map_object)

    if found_point is not None:
        folium.Marker(
            location=found_point,
            popup=_popup_html(
                title="Found Location",
                location=found_location,
                latitude=found_point[0],
                longitude=found_point[1],
                timestamp=found_timestamp,
            ),
            tooltip="Found Location",
            icon=folium.Icon(color="green", icon="ok-sign"),
        ).add_to(map_object)

    if last_seen_point is not None and found_point is not None:
        folium.PolyLine(
            locations=[last_seen_point, found_point],
            color="#0f766e",
            weight=4,
            opacity=0.85,
            tooltip="Last seen to found location",
        ).add_to(map_object)

    return map_object


def _coordinate_pair(latitude: Any, longitude: Any) -> tuple[float, float] | None:
    if latitude is None or longitude is None:
        return None
    try:
        parsed_latitude = float(latitude)
        parsed_longitude = float(longitude)
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= parsed_latitude <= 90.0 and -180.0 <= parsed_longitude <= 180.0):
        return None
    return parsed_latitude, parsed_longitude


def _popup_html(
    *,
    title: str,
    location: str | None,
    latitude: float,
    longitude: float,
    timestamp: str | None,
) -> str:
    return f"""
    <strong>{escape(title)}</strong><br>
    Location: {escape(location or "Not provided")}<br>
    Coordinates: {latitude:.6f}, {longitude:.6f}<br>
    Timestamp: {escape(timestamp or "Not provided")}
    """
