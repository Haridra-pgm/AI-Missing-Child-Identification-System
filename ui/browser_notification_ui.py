import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


BROWSER_NOTIFICATION_STATE_KEY = "pending_browser_notifications"


def queue_browser_notification(title: str, body: str) -> None:
    pending = st.session_state.setdefault(BROWSER_NOTIFICATION_STATE_KEY, [])
    pending.append({"title": title, "body": body})


def render_pending_browser_notifications() -> None:
    pending = st.session_state.pop(BROWSER_NOTIFICATION_STATE_KEY, [])
    if not pending:
        return

    for notification in pending:
        _render_browser_notification(notification)
        st.toast(notification["body"])


def _render_browser_notification(notification: dict[str, Any]) -> None:
    title_json = json.dumps(str(notification.get("title") or "ChildShield AI"))
    body_json = json.dumps(str(notification.get("body") or "Verified AI match update."))
    components.html(
        f"""
        <script>
        const title = {title_json};
        const body = {body_json};
        if ("Notification" in window) {{
            if (Notification.permission === "granted") {{
                new Notification(title, {{ body }});
            }} else if (Notification.permission !== "denied") {{
                Notification.requestPermission().then((permission) => {{
                    if (permission === "granted") {{
                        new Notification(title, {{ body }});
                    }}
                }});
            }}
        }}
        </script>
        """,
        height=0,
        width=0,
    )
