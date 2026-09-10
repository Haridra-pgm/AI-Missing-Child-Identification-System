from typing import Any

import streamlit as st

from services.location_service import find_nearby_police_stations
from ui.theme import display_value
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)


def render_nearby_police_stations(
    *,
    found_latitude: float | None,
    found_longitude: float | None,
    key_prefix: str,
) -> None:
    if found_latitude is None or found_longitude is None:
        return

    st.markdown("**Nearby Police Stations**")
    try:
        with st.spinner("Looking up nearby police stations..."):
            stations = find_nearby_police_stations(found_latitude, found_longitude)
    except ValidationError as exc:
        st.warning(str(exc))
        return
    except Exception:
        st.warning("Nearby police stations could not be loaded right now.")
        logger.exception("Police station lookup failed latitude=%s longitude=%s", found_latitude, found_longitude)
        return

    if not stations:
        st.info("No nearby police stations were found from OpenStreetMap for this location.")
        return

    rows = [
        {
            "Station": station["name"],
            "Address": display_value(station.get("address")),
            "Distance": f"{station['distance_km']:.2f} km",
            "Phone": display_value(station.get("phone")),
        }
        for station in stations
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    for index, station in enumerate(stations, start=1):
        st.link_button(
            f"Navigate to {station['name']}",
            station["navigation_link"],
            use_container_width=True,
        )
