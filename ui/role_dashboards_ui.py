from pathlib import Path
from typing import Any
from html import escape

import streamlit as st

from config.constants import FOUND_REPORT_STATUS_VERIFIED, FOUND_REPORT_STATUSES
from services.dashboard_service import DashboardDatabaseError, get_child_case_details
from services.role_dashboard_service import (
    RoleDashboardError,
    change_found_report_status,
    get_authority_dashboard,
    get_finder_dashboard,
    get_parent_dashboard,
    mark_user_notification_read,
)
from ui.browser_notification_ui import queue_browser_notification, render_pending_browser_notifications
from ui.location_map_ui import render_location_map
from ui.police_station_ui import render_nearby_police_stations
from ui.qr_ui import render_case_qr_tools
from ui.theme import display_value, format_datetime, render_kpi_cards, render_page_header
from ui.timeline_ui import render_case_timeline
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)


def render_parent_dashboard_page(user: dict[str, Any]) -> None:
    render_page_header(
        "Parent Dashboard",
        "Track your registered cases, missing-day counters, image evidence, and AI match notifications.",
    )
    try:
        data = get_parent_dashboard(user)
    except (ValidationError, RoleDashboardError) as exc:
        st.error(str(exc))
        logger.exception("Parent dashboard failed")
        return

    cases = data["cases"]
    notifications = data["notifications"]
    matched_reports = data["matched_reports"]

    render_kpi_cards(
        [
            ("My Cases", len(cases)),
            ("Open Alerts", sum(1 for item in notifications if not item["is_read"])),
            ("Matched Reports", len(matched_reports)),
        ]
    )
    _render_notifications(user, notifications)
    _render_parent_cases(cases)
    _render_parent_report_history(matched_reports)


def render_finder_dashboard_page(user: dict[str, Any]) -> None:
    render_page_header(
        "Child Finder Dashboard",
        "Review submitted found-child reports and AI match outcomes.",
    )
    try:
        data = get_finder_dashboard(user)
    except (ValidationError, RoleDashboardError) as exc:
        st.error(str(exc))
        logger.exception("Finder dashboard failed")
        return

    reports = data["reports"]
    render_kpi_cards(
        [
            ("Reports Submitted", len(reports)),
            ("Reports With Matches", sum(1 for report in reports if report["matches_found"] > 0)),
            ("Pending Verification", sum(1 for report in reports if report["status"] == "pending_verification")),
        ]
    )
    _render_notifications(user, data["notifications"])
    _render_found_reports(reports, allow_status_update=False, user=user)


def render_authority_dashboard_page(user: dict[str, Any]) -> None:
    render_page_header(
        "Authority Dashboard",
        "Review system analytics, active found-child reports, AI matches, and verification status.",
    )
    render_pending_browser_notifications()
    try:
        data = get_authority_dashboard(user)
    except (ValidationError, RoleDashboardError) as exc:
        st.error(str(exc))
        logger.exception("Authority dashboard failed")
        return

    statistics = data["overview"]["statistics"]
    render_kpi_cards(
        [
            ("Registered Children", statistics["total_registered_children"]),
            ("Search Requests", statistics["total_search_requests"]),
            ("Successful Matches", statistics["total_successful_matches"]),
            ("Found Reports", len(data["found_reports"])),
            ("Open Alerts", sum(1 for item in data["notifications"] if not item["is_read"])),
        ]
    )
    _render_notifications(user, data["notifications"])
    _render_found_reports(data["found_reports"], allow_status_update=True, user=user)


def _render_notifications(user: dict[str, Any], notifications: list[dict[str, Any]]) -> None:
    st.subheader("Notifications")
    if not notifications:
        st.info("No notifications yet.")
        return

    for notification in notifications[:10]:
        status = "Unread" if not notification["is_read"] else "Read"
        notification_class = "app-notification-read" if notification["is_read"] else "app-notification-unread"
        st.markdown(
            f"""
            <div class="app-notification-card {notification_class}">
                <div class="app-notification-title">{escape(str(notification['title']))}</div>
                <div class="app-notification-meta">
                    {_status_badge(status)}
                    <span style="margin-left:.5rem;">{escape(format_datetime(notification['created_at']))}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(
            f"View notification details - {status}",
            expanded=not notification["is_read"],
        ):
            st.markdown(_status_badge(status), unsafe_allow_html=True)
            st.write(notification["message"])
            st.caption(f"Case ID: {display_value(notification.get('case_id'))}")
            if not notification["is_read"]:
                if st.button("Mark as Read", key=f"mark_notification_{notification['notification_id']}"):
                    try:
                        mark_user_notification_read(user, int(notification["notification_id"]))
                        st.rerun()
                    except RoleDashboardError as exc:
                        st.error(str(exc))


def _render_parent_cases(cases: list[dict[str, Any]]) -> None:
    st.subheader("My Registered Cases")
    if not cases:
        st.info("No cases are linked to this parent account yet. Register a case from the sidebar.")
        return

    table_rows = [
        {
            "Case ID": case["case_id"],
            "Child Name": case["full_name"],
            "Age": case["age"],
            "Status": case["status"],
            "Missing Days": case["missing_days"],
            "Last Seen": case["last_seen_date"],
            "Images": case["uploaded_image_count"],
        }
        for case in cases
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    for case in cases:
        with st.expander(f"{case['case_id']} - {case['full_name']}", expanded=False):
            detail_col, metric_col = st.columns([2, 1])
            with detail_col:
                st.write(f"Status: {display_value(case['status'])}")
                st.write(f"Last seen date: {display_value(case['last_seen_date'])}")
                st.write(f"Last seen time: {display_value(case['last_seen_time'])}")
                st.write(f"Last seen location: {display_value(case['last_seen_location'])}")
                st.write(f"Registration date: {format_datetime(case['registration_date'])}")
            with metric_col:
                st.metric("Missing For", f"{case['missing_days']} days")
            _render_case_last_seen_map(case, key_prefix="parent_case")
            _render_image_gallery(case.get("images", []))
            render_case_qr_tools(case, key_prefix="parent_case")
            render_case_timeline(case.get("timeline"))


def _render_parent_report_history(reports: list[dict[str, Any]]) -> None:
    st.subheader("AI Match Search History")
    if not reports:
        st.info("No found-child reports have matched your linked cases yet.")
        return

    rows = [
        {
            "Report ID": report["report_id"],
            "Location": report["location"],
            "Matches": report["matches_found"],
            "Best Similarity": f"{report['best_similarity_score'] * 100:.2f}%",
            "Result": _report_result_label(report),
            "Status": _format_status_text(report["status"]),
            "Date": format_datetime(report["created_at"]),
        }
        for report in reports
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_found_reports(reports: list[dict[str, Any]], allow_status_update: bool, user: dict[str, Any]) -> None:
    st.subheader("Found Child Reports")
    if not reports:
        st.info("No found-child reports available.")
        return

    rows = [
        {
            "Report ID": report["report_id"],
            "Reporter": report["reporter_name"],
            "Location": report["location"],
            "Result": _report_result_label(report),
            "Matches": report["matches_found"],
            "Best Similarity": f"{report['best_similarity_score'] * 100:.2f}%",
            "Status": _format_status_text(report["status"]),
            "Submitted": format_datetime(report["created_at"]),
        }
        for report in reports
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    for report in reports:
        badge_html = _report_status_badge(report)
        st.markdown(
            f"""
            <div class="app-report-card">
                <div class="app-report-card-header">
                    <strong>Report {int(report['report_id'])} - {escape(str(report['location']))}</strong>
                    {badge_html}
                </div>
                <div class="app-report-meta">
                    Submitted {escape(format_datetime(report['created_at']))} by {escape(display_value(report['reporter_name']))}
                    | Best similarity {report['best_similarity_score'] * 100:.2f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"View Details - Report {report['report_id']}", expanded=False):
            image_col, detail_col = st.columns([1, 2])
            with image_col:
                image_path = report.get("absolute_image_path")
                if image_path and Path(image_path).exists():
                    st.image(image_path, caption="Reported found child image", use_container_width=True)
                else:
                    st.info("Reported image unavailable.")
            with detail_col:
                st.write(f"Reporter: {display_value(report['reporter_name'])}")
                st.write(f"Location: {display_value(report['location'])}")
                st.write(f"Description: {display_value(report['description'])}")
                st.write(f"Result: {_report_result_label(report)}")
                st.write(f"Matches found: {report['matches_found']}")
                st.write(f"Best similarity: {report['best_similarity_score'] * 100:.2f}%")
                st.write(f"Status: {_format_status_text(report['status'])}")
                st.write(f"Submitted: {format_datetime(report['created_at'])}")

            _render_report_matches(report.get("matches", []), show_qr_tools=allow_status_update)
            _render_report_location_map(report)
            if int(report.get("matches_found") or 0) > 0:
                render_nearby_police_stations(
                    found_latitude=report.get("found_latitude"),
                    found_longitude=report.get("found_longitude"),
                    key_prefix=f"report_{report['report_id']}",
                )
            if allow_status_update:
                _render_status_update(user, report)


def _render_report_matches(matches: list[dict[str, Any]], *, show_qr_tools: bool = False) -> None:
    if not matches:
        st.info("No threshold-qualified AI matches for this report.")
        return

    st.markdown("**AI Match Candidates**")
    for match in matches:
        st.write(
            f"Rank {match['match_rank']}: {match['case_id']} - {match['child_name']} "
            f"({match['similarity_percentage']:.2f}%)"
        )
        if show_qr_tools:
            _render_match_case_qr_tools(match)


def _render_match_case_qr_tools(match: dict[str, Any]) -> None:
    try:
        case_details = get_child_case_details(int(match["child_id"]))
    except (ValidationError, DashboardDatabaseError):
        logger.exception("Unable to load matched case QR tools child_id=%s", match.get("child_id"))
        return
    render_case_qr_tools(case_details, key_prefix=f"authority_match_{match['report_match_id']}")


def _render_case_last_seen_map(case: dict[str, Any], key_prefix: str) -> None:
    if case.get("last_seen_latitude") is None or case.get("last_seen_longitude") is None:
        return

    st.markdown("**Last Seen Location Map**")
    render_location_map(
        last_seen_location=case.get("last_seen_location"),
        last_seen_latitude=case.get("last_seen_latitude"),
        last_seen_longitude=case.get("last_seen_longitude"),
        last_seen_timestamp=_last_seen_timestamp(case),
        key=f"{key_prefix}_{case['child_id']}",
    )


def _render_report_location_map(report: dict[str, Any]) -> None:
    matches = report.get("matches") or []
    selected_match = next(
        (
            match
            for match in matches
            if match.get("last_seen_latitude") is not None and match.get("last_seen_longitude") is not None
        ),
        None,
    )

    has_found_coordinates = report.get("found_latitude") is not None and report.get("found_longitude") is not None
    if selected_match is None and not has_found_coordinates:
        return

    st.markdown("**Location Map**")
    render_location_map(
        last_seen_location=selected_match.get("last_seen_location") if selected_match else None,
        last_seen_latitude=selected_match.get("last_seen_latitude") if selected_match else None,
        last_seen_longitude=selected_match.get("last_seen_longitude") if selected_match else None,
        last_seen_timestamp=_last_seen_timestamp(selected_match) if selected_match else None,
        found_location=report.get("location"),
        found_latitude=report.get("found_latitude"),
        found_longitude=report.get("found_longitude"),
        found_timestamp=format_datetime(report.get("created_at")),
        key=f"report_location_map_{report['report_id']}",
    )


def _last_seen_timestamp(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    date_value = display_value(record.get("last_seen_date"))
    time_value = display_value(record.get("last_seen_time"))
    if time_value == "Not provided":
        return date_value
    return f"{date_value} {time_value}"


def _render_status_update(user: dict[str, Any], report: dict[str, Any]) -> None:
    status = st.selectbox(
        "Verification status",
        FOUND_REPORT_STATUSES,
        index=FOUND_REPORT_STATUSES.index(report["status"])
        if report["status"] in FOUND_REPORT_STATUSES
        else 0,
        key=f"report_status_{report['report_id']}",
    )
    if st.button("Update Report Status", key=f"update_report_{report['report_id']}"):
        try:
            result = change_found_report_status(user, int(report["report_id"]), status)
            if result["status"] == FOUND_REPORT_STATUS_VERIFIED and result.get("verified_matches"):
                _queue_verified_match_notifications(result["verified_matches"])
            st.success("Report status updated.")
            st.rerun()
        except ValidationError as exc:
            st.error(str(exc))
        except RoleDashboardError as exc:
            st.error(str(exc))


def _queue_verified_match_notifications(matches: list[dict[str, Any]]) -> None:
    for match in matches:
        queue_browser_notification(
            title="Verified AI match",
            body=(
                f"Case {match['case_id']} - {match['child_name']} verified "
                f"at {match['similarity_percentage']:.2f}% similarity."
            ),
        )


def _render_image_gallery(images: list[dict[str, Any]]) -> None:
    if not images:
        st.info("No registered images available.")
        return

    columns = st.columns(min(len(images), 3))
    for index, image in enumerate(images):
        image_path = image.get("absolute_image_path")
        with columns[index % len(columns)]:
            if image_path and Path(image_path).exists():
                st.image(image_path, caption=image["original_filename"], use_container_width=True)
            else:
                st.info("Image unavailable.")


def _report_result_label(report: dict[str, Any]) -> str:
    return "Match Found" if int(report.get("matches_found") or 0) > 0 else "No Match"


def _report_status_badge(report: dict[str, Any]) -> str:
    if int(report.get("matches_found") or 0) > 0:
        return _status_badge("Match Found", "app-status-match")
    return _status_badge("No Match", "app-status-no-match")


def _status_badge(label: str, extra_class: str = "") -> str:
    css_class = f"app-status-badge {extra_class}".strip()
    return f'<span class="{css_class}">{escape(label)}</span>'


def _format_status_text(value: Any) -> str:
    text = str(value or "").replace("_", " ").strip()
    return text.title() if text else "Not provided"
