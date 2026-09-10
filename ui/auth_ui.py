import base64
from typing import Any

import streamlit as st

from config.constants import ROLE_AUTHORITY, ROLE_FINDER, ROLE_LABELS, ROLE_PARENT
from services.auth_service import (
    DEFAULT_USERS,
    AuthenticationError,
    AuthorizationError,
    authenticate_user,
)
from ui.theme import LOGO_PATH
from utils.logger import get_logger
from utils.validators import ValidationError


logger = get_logger(__name__)

AUTH_USER_STATE_KEY = "auth_user"
LOGIN_ROLE_STATE_KEY = "login_role"
PORTAL_LABELS = {
    ROLE_PARENT: "Parent Portal",
    ROLE_FINDER: "Child Finder Portal",
    ROLE_AUTHORITY: "Authority Portal",
}


def get_authenticated_user() -> dict[str, Any] | None:
    user = st.session_state.get(AUTH_USER_STATE_KEY)
    return user if isinstance(user, dict) else None


def logout_user() -> None:
    st.session_state.pop(AUTH_USER_STATE_KEY, None)
    st.session_state.pop(LOGIN_ROLE_STATE_KEY, None)
    st.rerun()


def render_public_home_page() -> None:
    _render_hero()
    _render_login_section()


def _render_hero() -> None:
    logo_html = ""
    if LOGO_PATH.exists():
        logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        logo_html = f'<img src="data:image/svg+xml;base64,{logo_data}" alt="ChildShield AI logo" />'

    st.markdown(
        f"""
        <div class="app-home-hero">
            <div class="app-home-card">
                <div class="app-home-brand">
                    {logo_html}
                </div>
                <h1>AI-Based Missing Child Identification &amp; Recovery System</h1>
                <p>
                    Helping families and authorities identify and recover missing children using AI-assisted face matching.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_login_section() -> None:
    with st.container(border=True):
        st.markdown('<div class="app-login-title">Select Your Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-portal-actions">', unsafe_allow_html=True)
        role_cols = st.columns(3)
        role_sequence = [ROLE_PARENT, ROLE_FINDER, ROLE_AUTHORITY]
        for column, role in zip(role_cols, role_sequence):
            with column:
                label = PORTAL_LABELS[role]
                if st.button(label, use_container_width=True):
                    st.session_state[LOGIN_ROLE_STATE_KEY] = role
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        selected_role = st.session_state.get(LOGIN_ROLE_STATE_KEY, ROLE_PARENT)
        _render_login_form(selected_role)


def _render_login_form(role: str) -> None:
    demo_user = next(user for user in DEFAULT_USERS if user["role"] == role)
    with st.form(f"login_form_{role}"):
        st.markdown(f"#### {PORTAL_LABELS[role]} Login")
        email = st.text_input("Email", value=demo_user["email"], max_chars=120)
        password = st.text_input("Password", type="password", value=demo_user["password"], max_chars=80)
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    st.caption(f"Demo credentials: {demo_user['email']} / {demo_user['password']}")

    if not submitted:
        return

    try:
        with st.spinner("Signing in securely..."):
            user = authenticate_user(email, password, role)
        st.session_state[AUTH_USER_STATE_KEY] = user
        st.success(f"Signed in as {ROLE_LABELS[user['role']]}.")
        st.rerun()
    except ValidationError as exc:
        st.error(str(exc))
    except AuthorizationError as exc:
        st.warning(str(exc))
    except AuthenticationError as exc:
        st.error(str(exc))
        logger.info("Login failed for role=%s email=%s", role, email)
    except Exception:
        st.error("Login failed. Please check the logs and try again.")
        logger.exception("Unexpected login UI failure")
