from config.constants import ROLE_AUTHORITY, ROLE_FINDER, ROLE_PARENT
from database.schema import initialize_database
from services.auth_service import ensure_default_users
from ui.age_progression_ui import render_age_progression_page
from ui.auth_ui import get_authenticated_user, logout_user, render_public_home_page
from ui.dashboard_ui import render_admin_dashboard_page, render_linked_case_details_page
from ui.found_report_ui import render_found_child_report_page
from ui.records_ui import render_records_page
from ui.registration_ui import render_registration_page
from ui.role_dashboards_ui import (
    render_authority_dashboard_page,
    render_finder_dashboard_page,
    render_parent_dashboard_page,
)
from ui.search_ui import render_found_child_search_page
from ui.theme import LOGO_PATH, apply_app_theme, render_sidebar_brand
from utils.logger import get_logger

import streamlit as st


logger = get_logger(__name__)
DEFAULT_USERS_READY_KEY = "default_role_users_ready"
PORTAL_LABELS = {
    ROLE_PARENT: "Parent Portal",
    ROLE_FINDER: "Child Finder Portal",
    ROLE_AUTHORITY: "Authority Portal",
}


def main() -> None:
    st.set_page_config(
        page_title="ChildShield AI",
        page_icon=str(LOGO_PATH),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_app_theme()

    try:
        initialize_database()
        if not st.session_state.get(DEFAULT_USERS_READY_KEY):
            ensure_default_users()
            st.session_state[DEFAULT_USERS_READY_KEY] = True
    except Exception:
        logger.exception("Application startup failed while initializing the database")
        st.error("Database initialization failed. Check the application logs and try again.")
        return

    user = get_authenticated_user()
    if user is None:
        render_public_home_page()
        return

    render_sidebar_brand()
    st.sidebar.markdown(
        f'<div class="app-sidebar-portal">{PORTAL_LABELS[user["role"]]}</div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()

    linked_case_id = _get_linked_case_id()
    navigation = _navigation_for_role(user["role"], linked_case_id)
    selected_page = st.sidebar.radio("Navigation", list(navigation.keys()))
    navigation[selected_page](user)


def _navigation_for_role(role: str, linked_case_id: str | None = None):
    linked_case_navigation = (
        {"QR Case Details": lambda user: render_linked_case_details_page(user, linked_case_id)}
        if linked_case_id and role in {ROLE_PARENT, ROLE_AUTHORITY}
        else {}
    )
    if role == ROLE_PARENT:
        return {
            **linked_case_navigation,
            "Parent Dashboard": render_parent_dashboard_page,
            "Register Missing Child": lambda user: render_registration_page(registered_by_user_id=user["user_id"]),
        }

    if role == ROLE_FINDER:
        return {
            "Child Finder Dashboard": render_finder_dashboard_page,
            "Report Found Child": render_found_child_report_page,
            "Found Child Search": lambda user: render_found_child_search_page(),
        }

    if role == ROLE_AUTHORITY:
        return {
            **linked_case_navigation,
            "Authority Dashboard": render_authority_dashboard_page,
            "Register Missing Child": lambda user: render_registration_page(),
            "View Records": lambda user: render_records_page(),
            "Found Child Search": lambda user: render_found_child_search_page(),
            "AI Age Progression": lambda user: render_age_progression_page(),
            "Admin Dashboard": lambda user: render_admin_dashboard_page(),
        }

    return {"Home": lambda user: render_public_home_page()}


def _get_linked_case_id() -> str | None:
    value = st.query_params.get("case_id")
    if isinstance(value, list):
        value = value[0] if value else None
    cleaned = " ".join(str(value or "").split())
    return cleaned or None


if __name__ == "__main__":
    main()
