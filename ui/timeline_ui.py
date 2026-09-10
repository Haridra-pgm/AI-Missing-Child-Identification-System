from html import escape
from typing import Any

import streamlit as st

from ui.theme import format_datetime


def render_case_timeline(timeline_events: list[dict[str, Any]] | None) -> None:
    st.markdown("**Case Timeline**")
    if not timeline_events:
        st.info("No timeline events recorded for this case yet.")
        return

    for event in timeline_events:
        title = escape(str(event.get("event_title") or "Case Event"))
        timestamp = escape(format_datetime(event.get("created_at")))
        description = escape(str(event.get("event_description") or ""))
        st.markdown(
            f"""
            <div class="app-card" style="margin-bottom:.65rem;">
                <div style="font-weight:700;color:#0f172a;">{title}</div>
                <div style="font-size:.85rem;color:#64748b;margin:.15rem 0 .35rem;">{timestamp}</div>
                <div style="color:#334155;">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
