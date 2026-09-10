from pathlib import Path
from typing import Any

import streamlit as st

from services.role_dashboard_service import RoleDashboardError, submit_found_child_report
from ui.location_map_ui import render_location_map
from ui.police_station_ui import render_nearby_police_stations
from ui.theme import display_value, render_page_header
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)


def render_found_child_report_page(user: dict[str, Any]) -> None:
    render_page_header(
        "Report Found Child",
        "Submit a found-child report and run AI-assisted matching against registered cases.",
    )

    with st.form("found_child_report_form", clear_on_submit=False):
        uploaded_image = st.file_uploader(
            "Upload found child image",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            help="Use one clear image with one visible face.",
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Found child image preview", width=260)

        location = st.text_input(
            "Found location",
            max_chars=200,
            placeholder="Area, landmark, city, state",
            help="Enter a specific location. The app will find map coordinates automatically.",
        )
        description = st.text_area(
            "Description",
            max_chars=500,
            height=120,
            placeholder="Clothing, condition, nearby details, and any urgent context",
        )
        submitted = st.form_submit_button("Submit Report and Run AI Match", type="primary", use_container_width=True)

    if not submitted:
        return

    try:
        with st.spinner("Saving report, generating SFace embedding, searching cases, and sending alerts..."):
            result = submit_found_child_report(
                user,
                uploaded_image,
                location,
                description,
                require_location_geocode=True,
            )

        st.success(f"Found-child report submitted. Report ID: {result['report_id']}")
        st.caption(
            f"Search ID: {result['search_id']} | Matches found: {result['matches_found']} | "
            f"Best similarity: {result['best_similarity_score'] * 100:.2f}% | "
            f"Notifications created: {result['notification_count']}"
        )

        if not result["matches"]:
            st.warning("No matching child found above the configured threshold.")
            return

        st.subheader("AI Match Results")
        _render_report_matches(
            result["matches"],
            found_location=result.get("found_location"),
            found_latitude=result.get("found_latitude"),
            found_longitude=result.get("found_longitude"),
        )
        render_nearby_police_stations(
            found_latitude=result.get("found_latitude"),
            found_longitude=result.get("found_longitude"),
            key_prefix=f"submitted_report_{result['report_id']}",
        )
    except ValidationError as exc:
        st.error(f"Please correct the found-child report details: {exc}")
        logger.info("Found report validation failed: %s", exc)
    except RoleDashboardError as exc:
        st.error(str(exc))
        logger.exception("Found report service failed")
    except Exception:
        st.error("Found-child report could not be submitted. Please check the logs and try again.")
        logger.exception("Unexpected found report UI failure")


def _render_report_matches(
    matches: list[dict[str, Any]],
    *,
    found_location: str | None = None,
    found_latitude: float | None = None,
    found_longitude: float | None = None,
) -> None:
    for index, match in enumerate(matches, start=1):
        st.markdown(
            f"""
            <div class="app-match-card {'app-best-match' if index == 1 else ''}">
                <span class="app-pill">{'Best Match' if index == 1 else f'Rank {index}'}</span>
                <strong style="margin-left:.45rem;">{match['case_id']} - {match['child_name']}</strong>
                <div style="margin-top:.45rem;color:#334155;">
                    Similarity: <strong>{match['similarity_percentage']:.2f}%</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        image_path = match.get("stored_image_path")
        with st.expander(f"Review match details for {match['case_id']}", expanded=index == 1):
            image_col, details_col = st.columns([1, 2])
            with image_col:
                if image_path and Path(image_path).exists():
                    st.image(image_path, caption="Registered child image", use_container_width=True)
                else:
                    st.info("Stored child image unavailable.")
            with details_col:
                st.write(f"Case ID: {display_value(match.get('case_id'))}")
                st.write(f"Child Name: {display_value(match.get('child_name'))}")
                st.write(f"Age: {display_value(match.get('age'))}")
                st.write(f"Gender: {display_value(match.get('gender'))}")
                st.write(f"Guardian: {display_value(match.get('guardian_name'))}")
                st.write(f"Contact: {display_value(match.get('contact_number'))}")
                st.write(f"Similarity: {match['similarity_percentage']:.2f}%")
            _render_match_location_map(match, found_location, found_latitude, found_longitude, index)


def _render_match_location_map(
    match: dict[str, Any],
    found_location: str | None,
    found_latitude: float | None,
    found_longitude: float | None,
    index: int,
) -> None:
    has_last_seen = match.get("last_seen_latitude") is not None and match.get("last_seen_longitude") is not None
    has_found = found_latitude is not None and found_longitude is not None
    if not has_last_seen and not has_found:
        return

    st.markdown("**Location Map**")
    render_location_map(
        last_seen_location=match.get("last_seen_location"),
        last_seen_latitude=match.get("last_seen_latitude"),
        last_seen_longitude=match.get("last_seen_longitude"),
        last_seen_timestamp=_last_seen_timestamp(match),
        found_location=found_location,
        found_latitude=found_latitude,
        found_longitude=found_longitude,
        found_timestamp="Submitted now",
        key=f"submitted_report_map_{index}_{match.get('child_id')}",
    )


def _last_seen_timestamp(match: dict[str, Any]) -> str | None:
    date_value = display_value(match.get("last_seen_date"))
    time_value = display_value(match.get("last_seen_time"))
    if date_value == "Not provided":
        return None
    if time_value == "Not provided":
        return date_value
    return f"{date_value} {time_value}"
