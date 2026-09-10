from typing import Any

import streamlit as st

from services.qr_service import QRCodeGenerationError, build_printable_case_report_html, generate_case_qr_png
from utils.logger import get_logger


logger = get_logger(__name__)


def render_case_qr_tools(case_details: dict[str, Any], *, key_prefix: str) -> None:
    st.markdown("**Case QR Code**")
    try:
        qr_png = generate_case_qr_png(case_details["case_id"])
        report_html = build_printable_case_report_html(case_details)
    except QRCodeGenerationError as exc:
        st.warning(str(exc))
        logger.info("QR generation unavailable case_id=%s error=%s", case_details.get("case_id"), exc)
        return
    except Exception:
        st.warning("QR code could not be generated for this case.")
        logger.exception("Unexpected QR generation failure case_id=%s", case_details.get("case_id"))
        return

    with st.container(border=True):
        qr_col, download_col = st.columns([0.55, 1.45])
        with qr_col:
            st.image(qr_png, caption=f"Case {case_details['case_id']}", width=150)
        with download_col:
            st.download_button(
                "Download QR Code",
                data=qr_png,
                file_name=f"{case_details['case_id']}_qr.png",
                mime="image/png",
                use_container_width=True,
                key=f"{key_prefix}_qr_download_{case_details['child_id']}",
            )
            st.download_button(
                "Download Printable Case Report",
                data=report_html,
                file_name=f"{case_details['case_id']}_case_report.html",
                mime="text/html",
                use_container_width=True,
                key=f"{key_prefix}_report_download_{case_details['child_id']}",
            )
