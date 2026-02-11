"""
utils/qr_engine.py
────────────────────────────────────────────
Zentrale QR-Engine für Ouhud QR.
- Unterstützt: URL, vCard, Wi-Fi, PDF, E-Mail, SMS, Social
- Nutzt: utils/qr_config und utils/qr_generator
- Gibt Dictionary {"path": "...", "bytes": b"..."} zurück
────────────────────────────────────────────
"""

from typing import Optional, Dict, Any
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png
import logging

logger = logging.getLogger(__name__)


def build_qr_code(
    qr_type: str,
    data: Dict[str, Any],
    style_name: str = "modern",
    qr_size: int = 600,
    color_fg: Optional[str] = None,
    color_bg: Optional[str] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "center",
) -> Dict[str, Any]:
    """
    Erstellt einen QR-Code (z. B. URL, Wi-Fi, vCard, PDF, SMS) und gibt
    ein Dictionary mit {"path": "...", "bytes": b"..."} zurück.
    """

    # 1️⃣ Stilkonfiguration laden
    style = get_qr_style(style_name)
    fg = color_fg or style["fg"]
    bg = color_bg or style["bg"]
    gradient = style.get("gradient")

    # 2️⃣ QR-Inhalt generieren
    qr_type = qr_type.lower()
    if qr_type == "url":
        payload = data.get("url", "")
    elif qr_type == "wifi":
        payload = (
            f"WIFI:T:{data.get('encryption', 'WPA')};"
            f"S:{data.get('ssid', '')};"
            f"P:{data.get('password', '')};"
            f"H:{'true' if data.get('hidden') else 'false'};;"
        )
    elif qr_type == "vcard":
        payload = f"""
BEGIN:VCARD
VERSION:3.0
FN:{data.get("name", "")}
ORG:{data.get("organization", "")}
TITLE:{data.get("title", "")}
TEL;TYPE=WORK,VOICE:{data.get("phone", "")}
EMAIL:{data.get("email", "")}
URL:{data.get("website", "")}
ADR;TYPE=WORK:{data.get("address", "")}
END:VCARD
""".strip()
    elif qr_type == "email":
        payload = f"mailto:{data.get('email', '')}?subject={data.get('subject', '')}&body={data.get('body', '')}"
    elif qr_type == "sms":
        payload = f"SMSTO:{data.get('phone', '')}:{data.get('message', '')}"
    elif qr_type == "pdf":
        payload = data.get("url", "")
    elif qr_type == "social":
        payload = data.get("url", "")
    else:
        payload = str(data)
        logger.warning(f"⚠️ Unbekannter QR-Typ: {qr_type}")

    # 3️⃣ QR-Code generieren
    qr_result = generate_qr_png(
        payload=payload,
        size=qr_size,
        fg=fg,
        bg=bg,
        gradient=gradient,
        logo_path=logo_path,
        logo_position=logo_position,
        frame_color=str(style.get("frame_color", "#4F46E5")),
        module_style=style.get("module_style", "square"),
        eye_style=style.get("eye_style", "square"),
        frame_text=style.get("frame_text"),
    )

    logger.info(f"✅ QR-Code erfolgreich erstellt: {qr_result['path']}")
    return qr_result
