from html import escape
from typing import Any

import streamlit as st

from config.settings import BASE_DIR


APP_NAME = "ChildShield AI"
APP_SUBTITLE = "Missing Child Identification"
LOGO_PATH = BASE_DIR / "assets" / "app_logo.svg"


def apply_app_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-primary: #2D9C8C;
            --app-primary-dark: #23897C;
            --app-accent: #2D9C8C;
            --app-bg: #EAF7F2;
            --app-soft-bg: #DFF3EB;
            --app-sidebar-bg: #D8F0E8;
            --app-hero-bg: #CDEDE2;
            --app-surface: #FFFFFF;
            --app-card-bg: #FFFFFF;
            --app-muted: #64748b;
            --app-border: #A8DCCB;
            --app-text: #1F2937;
            --app-danger: #b91c1c;
            --app-shadow: 0 16px 42px rgba(45, 156, 140, 0.11);
            --app-shadow-soft: 0 8px 24px rgba(45, 156, 140, 0.08);
        }

        html, body, .stApp {
            background: linear-gradient(180deg, #EAF7F2 0%, #DFF3EB 100%);
            color: var(--app-text);
            font-family: "Inter", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .block-container {
            max-width: 1240px;
            padding-top: 0.45rem;
            padding-bottom: 2.5rem;
        }

        [data-testid="stSidebar"] {
            background: var(--app-sidebar-bg);
            border-right: 1px solid var(--app-border);
        }

        [data-testid="stSidebar"] img {
            margin-top: 0.25rem;
        }

        .app-brand-title {
            color: var(--app-text);
            font-size: 1.08rem;
            font-weight: 750;
            line-height: 1.15;
            margin: 0.25rem 0 0;
        }

        .app-brand-subtitle {
            color: var(--app-muted);
            font-size: 0.78rem;
            margin-bottom: 1.1rem;
        }

        .app-sidebar-portal {
            border: 1px solid var(--app-border);
            background: #ffffff;
            border-radius: 18px;
            color: var(--app-text);
            font-size: 0.94rem;
            font-weight: 800;
            margin: 0.25rem 0 0.9rem;
            padding: 0.75rem 0.85rem;
            text-align: center;
            box-shadow: var(--app-shadow-soft);
        }

        .app-page-header {
            border: 1px solid var(--app-border);
            background: var(--app-soft-bg);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1.1rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-page-header h1 {
            color: var(--app-text);
            font-size: 1.9rem;
            line-height: 1.2;
            margin: 0;
            letter-spacing: 0;
        }

        .app-page-header p {
            color: var(--app-muted);
            font-size: 0.95rem;
            margin: 0.3rem 0 0;
        }

        .app-card {
            border: 1px solid var(--app-border);
            background: var(--app-surface);
            border-radius: 20px;
            padding: 1.15rem;
            margin-bottom: 1rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-card-title {
            color: var(--app-text);
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 0.6rem;
        }

        .app-home-hero {
            max-width: 940px;
            margin: 0.45rem auto 1rem;
            border: 1px solid var(--app-border);
            background: var(--app-hero-bg);
            border-radius: 28px;
            padding: 1.15rem;
            text-align: center;
            box-shadow: var(--app-shadow);
        }

        .app-home-card {
            max-width: 760px;
            margin: 0 auto;
            border: 1px solid var(--app-border);
            background: #ffffff;
            border-radius: 24px;
            padding: 2.15rem 2rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-home-brand {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 1rem;
        }

        .app-home-brand img {
            width: 78px;
            height: 78px;
        }

        .app-home-hero h1 {
            color: var(--app-text);
            font-size: 2.35rem;
            line-height: 1.12;
            letter-spacing: 0;
            margin: 0 auto 0.8rem;
            max-width: 720px;
        }

        .app-home-hero p {
            color: #475569;
            font-size: 1.02rem;
            line-height: 1.65;
            max-width: 680px;
            margin: 0 auto;
        }

        .app-login-panel {
            max-width: 860px;
            margin: 0 auto 2rem;
            border: 1px solid var(--app-border);
            border-radius: 20px;
            background: #ffffff;
            padding: 1.15rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-login-title {
            color: var(--app-text);
            font-size: 1.15rem;
            font-weight: 800;
            margin: 0 0 0.75rem;
            text-align: center;
        }

        .app-role-icon {
            display: none;
        }

        .app-portal-actions {
            margin: 0.25rem 0 0.9rem;
        }

        .app-kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 1rem;
            margin: 0.7rem 0 1.15rem;
        }

        .app-kpi-card {
            border: 1px solid var(--app-border);
            background: #ffffff;
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-kpi-label {
            color: var(--app-muted);
            font-size: 0.78rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0;
        }

        .app-kpi-value {
            color: var(--app-text);
            font-size: 1.55rem;
            font-weight: 780;
            margin-top: 0.15rem;
        }

        .app-match-card {
            border: 1px solid var(--app-border);
            border-left: 5px solid var(--app-primary);
            border-radius: 20px;
            padding: 1.1rem 1.15rem;
            margin-bottom: 0.8rem;
            background: #ffffff;
            box-shadow: var(--app-shadow-soft);
        }

        .app-best-match {
            border-left-color: var(--app-accent);
            background: #f0f9ff;
        }

        .app-pill {
            display: inline-block;
            border: 1px solid #b7e4df;
            background: #ecfdf5;
            color: var(--app-primary-dark);
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .app-status-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.76rem;
            font-weight: 750;
            border: 1px solid var(--app-border);
            color: #334155;
            background: #f8fafc;
        }

        .app-status-match {
            border-color: #86efac;
            color: #166534;
            background: #f0fdf4;
        }

        .app-status-no-match {
            border-color: #fecaca;
            color: #991b1b;
            background: #fef2f2;
        }

        .app-status-pending {
            border-color: #bae6fd;
            color: #075985;
            background: #f0f9ff;
        }

        .app-report-card {
            border: 1px solid var(--app-border);
            background: #ffffff;
            border-radius: 20px;
            padding: 1.1rem 1.15rem;
            margin-bottom: 0.9rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-report-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 0.45rem;
        }

        .app-report-meta {
            color: var(--app-muted);
            font-size: 0.86rem;
        }

        .app-danger-note {
            border: 1px solid #fecaca;
            background: #fff1f2;
            color: #7f1d1d;
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.8rem;
        }

        .app-notification-card {
            border: 1px solid var(--app-border);
            border-radius: 20px;
            padding: 0.85rem 1rem;
            margin: 0.65rem 0 0.35rem;
            box-shadow: var(--app-shadow-soft);
        }

        .app-notification-unread {
            background: #F2FBF8;
            border-left: 5px solid var(--app-primary);
        }

        .app-notification-read {
            background: #ffffff;
            border-left: 5px solid #cbd5e1;
        }

        .app-notification-title {
            color: var(--app-text);
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .app-notification-meta {
            color: var(--app-muted);
            font-size: 0.86rem;
        }

        .app-map-card,
        .app-qr-card {
            border: 1px solid var(--app-border);
            border-radius: 20px;
            background: #ffffff;
            box-shadow: var(--app-shadow-soft);
            padding: 1rem;
            margin: 0.7rem 0 1rem;
        }

        div[data-testid="stForm"],
        div[data-testid="stFileUploader"] section {
            border-radius: 20px;
            border-color: var(--app-border);
            background: #ffffff;
        }

        div[data-testid="stForm"] {
            box-shadow: var(--app-shadow-soft);
            padding: 0.2rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--app-border);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: var(--app-shadow-soft);
        }

        div[data-testid="stDataFrame"] [role="grid"] {
            font-size: 0.92rem;
        }

        div[data-testid="stDataFrame"] div[role="row"]:nth-child(even) {
            background: #F2FBF8;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--app-border);
            border-radius: 20px;
            box-shadow: var(--app-shadow-soft);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--app-border) !important;
            border-radius: 20px !important;
            background: #ffffff;
            box-shadow: var(--app-shadow-soft);
            padding: 0.35rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 14px;
            border-color: var(--app-primary);
            background: #F2FBF8;
            color: var(--app-text);
            font-weight: 700;
            min-height: 2.6rem;
            padding: 0.45rem 1rem;
            transition: all 0.16s ease;
            box-shadow: 0 3px 10px rgba(45, 156, 140, 0.06);
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--app-primary);
            border-color: var(--app-primary);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: var(--app-primary-dark);
            background: #E8F7F2;
            color: var(--app-primary-dark);
            box-shadow: 0 6px 18px rgba(45, 156, 140, 0.12);
        }

        .stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--app-primary-dark);
            border-color: var(--app-primary-dark);
            color: #ffffff;
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
            border-color: var(--app-border);
            box-shadow: var(--app-shadow-soft);
        }

        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4 {
            color: var(--app-text);
            font-weight: 800;
        }

        div[data-testid="stMarkdownContainer"] h4 {
            margin-top: 0.55rem;
            margin-bottom: 0.55rem;
        }

        h1, h2, h3, h4 {
            letter-spacing: 0;
        }

        h2, h3 {
            margin-top: 1.15rem;
        }

        @media (max-width: 760px) {
            .app-page-header {
                padding: 0.9rem;
            }
            .app-page-header h1 {
                font-size: 1.45rem;
            }
            .app-home-hero {
                padding: 0.85rem;
                margin-top: 0.2rem;
            }
            .app-home-card {
                padding: 1.35rem 1rem;
            }
            .app-home-hero h1 {
                font-size: 1.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=72)
    st.sidebar.markdown(
        f"""
        <div class="app-brand-title">{APP_NAME}</div>
        <div class="app-brand-subtitle">{APP_SUBTITLE}</div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="app-page-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(items: list[tuple[str, Any]]) -> None:
    cards = "".join(
        '<div class="app-kpi-card">'
        f'<div class="app-kpi-label">{escape(str(label))}</div>'
        f'<div class="app-kpi-value">{escape(str(value))}</div>'
        "</div>"
        for label, value in items
    )
    st.markdown(f'<div class="app-kpi-grid">{cards}</div>', unsafe_allow_html=True)


def display_value(value: Any) -> str:
    if value is None:
        return "Not provided"
    if isinstance(value, str) and not value.strip():
        return "Not provided"
    return str(value)


def format_datetime(value: Any) -> str:
    if not value:
        return "Not provided"

    from datetime import datetime

    raw_value = str(value)
    try:
        parsed = datetime.fromisoformat(raw_value)
        return parsed.strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return raw_value
