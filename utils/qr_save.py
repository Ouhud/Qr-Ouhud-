# utils/qr_save.py
# =============================================================================
# ✅ PRO-Level: Einheitliche Speicherlogik für ALLE QR-Codes
# - automatische Validierung
# - Logging & Debug
# - Versionierung
# - Update-Historie
# =============================================================================

import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models.qrcode import QRCode
from models.qr_history import QRHistory
from utils.qr_schema import QR_SCHEMAS

logger = logging.getLogger("qr_save")
logger.setLevel(logging.INFO)


# =============================================================================
# ✅ Hilfsfunktion: Validierung der Daten
# =============================================================================
def validate_qr(qr_type: str, data: Dict[str, Any]):
    if qr_type not in QR_SCHEMAS:
        logger.warning(f"⚠️ Kein Schema für Typ '{qr_type}' definiert – Validierung übersprungen.")
        return

    schema = QR_SCHEMAS[qr_type]

    for req in schema.get("required", []):
        if req not in data or data[req] in ("", None):
            raise ValueError(f"❌ '{req}' ist erforderlich für QR-Typ '{qr_type}'")


# =============================================================================
# ✅ SPEICHERN
# =============================================================================
def save_qr(
    db: Session,
    user_id: int,
    qr_type: str,
    title: str,
    data: Dict[str, Any],
    slug: Optional[str] = None,
    image_path: Optional[str] = None,
    dynamic_url: Optional[str] = None,
    style: str = "classic",
    color_fg: str = "#000000",
    color_bg: str = "#FFFFFF",
    qr_size: int = 600,
    logo_path: Optional[str] = None,
    is_dynamic: bool = False
) -> QRCode:

    # ✅ Validierung
    validate_qr(qr_type, data)

    # ✅ Debug Log
    logger.info(f"📦 Speichere QR: type={qr_type}, user={user_id}, title={title}")

    qr = QRCode(
        user_id=user_id,
        type=qr_type,
        title=title,
        slug=slug,
        content=json.dumps(data, ensure_ascii=False),
        image_path=image_path,
        dynamic_url=dynamic_url,
        is_dynamic=is_dynamic,
        style=style,
        color_fg=color_fg,
        color_bg=color_bg,
        qr_size=qr_size,
        logo_path=logo_path,
        active=True
    )

    db.add(qr)
    db.commit()
    db.refresh(qr)

    # ✅ Versionierungseintrag
    history = QRHistory(
        qr_id=qr.id,
        user_id=user_id,
        action="create",
        old_data=None,
        new_data=json.dumps(data, ensure_ascii=False)
    )
    db.add(history)
    db.commit()

    logger.info(f"✅ QR-Code gespeichert (ID {qr.id}, slug={qr.slug})")

    return qr


# =============================================================================
# ✅ UPDATE
# =============================================================================
def update_qr(
    db: Session,
    qr: QRCode,
    user_id: int,
    new_data: Dict[str, Any],
):
    old_data = qr.content

    # ✅ Validierung
    validate_qr(qr.type, new_data)

    qr.content = json.dumps(new_data, ensure_ascii=False)
    db.commit()
    db.refresh(qr)

    # ✅ Historie speichern
    history = QRHistory(
        qr_id=qr.id,
        user_id=user_id,
        action="update",
        old_data=old_data,
        new_data=json.dumps(new_data, ensure_ascii=False)
    )
    db.add(history)
    db.commit()

    logger.info(f"✏️ QR-Code aktualisiert (ID {qr.id})")

    return qr