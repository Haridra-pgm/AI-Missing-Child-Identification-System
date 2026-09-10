import base64
from html import escape
from io import BytesIO
from typing import Any
from urllib.parse import quote

from config.settings import APP_PUBLIC_BASE_URL
from utils.logger import get_logger


logger = get_logger(__name__)


class QRCodeGenerationError(Exception):
    """Raised when a QR code cannot be generated."""


def build_case_url(case_id: str) -> str:
    safe_case_id = quote(str(case_id or "").strip())
    return f"{APP_PUBLIC_BASE_URL.rstrip('/')}/?case_id={safe_case_id}"


def generate_case_qr_png(case_id: str) -> bytes:
    try:
        import qrcode
    except ImportError as exc:
        raise QRCodeGenerationError("QR code dependency is not installed. Run pip install -r requirements.txt.") from exc

    if not str(case_id or "").strip():
        raise QRCodeGenerationError("Case ID is required to generate a QR code.")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(build_case_url(case_id))
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0f766e", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def build_printable_case_report_html(case_details: dict[str, Any]) -> bytes:
    qr_png = generate_case_qr_png(case_details["case_id"])
    qr_base64 = base64.b64encode(qr_png).decode("ascii")
    case_id = _html_value(case_details.get("case_id"))
    full_name = _html_value(case_details.get("full_name"))
    age = _html_value(case_details.get("age"))
    gender = _html_value(case_details.get("gender"))
    status = _html_value(case_details.get("status"))
    last_seen_location = _html_value(case_details.get("last_seen_location"))
    last_seen_date = _html_value(case_details.get("last_seen_date"))
    case_url = _html_value(build_case_url(case_details["case_id"]))
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ChildShield AI Case Report - {case_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; color: #0f172a; margin: 32px; }}
            h1 {{ color: #0f766e; margin-bottom: 4px; }}
            .muted {{ color: #64748b; }}
            .section {{ border: 1px solid #dbeafe; border-radius: 8px; padding: 16px; margin: 16px 0; }}
            .label {{ font-weight: 700; }}
            img {{ width: 180px; height: 180px; }}
        </style>
    </head>
    <body>
        <h1>ChildShield AI Case Report</h1>
        <p class="muted">Generated case access QR for authorized review.</p>
        <div class="section">
            <p><span class="label">Case ID:</span> {case_id}</p>
            <p><span class="label">Child Name:</span> {full_name}</p>
            <p><span class="label">Age:</span> {age}</p>
            <p><span class="label">Gender:</span> {gender}</p>
            <p><span class="label">Status:</span> {status}</p>
            <p><span class="label">Last Seen:</span> {last_seen_location} on {last_seen_date}</p>
        </div>
        <div class="section">
            <p class="label">Case QR Code</p>
            <img src="data:image/png;base64,{qr_base64}" alt="Case QR code">
            <p class="muted">{case_url}</p>
        </div>
    </body>
    </html>
    """
    return html.encode("utf-8")


def _html_value(value: Any) -> str:
    if value is None:
        return "Not provided"
    return escape(str(value))
