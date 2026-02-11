from __future__ import annotations
from typing import Dict, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from database import get_db
from models.qrcode import QRCode

# --------------------------------------------------------------------------- #
# 💾 Kontingent-Management für dynamische QR-Codes
# --------------------------------------------------------------------------- #

router = APIRouter(prefix="/quota", tags=["Quota"])

# 📊 Limits je nach Plan
PLAN_LIMITS: Dict[str, int] = {
    "free": 5,
    "basic": 20,
    "pro": 100,
    "business": 1000,
}


def get_user_quota_internal(db: Session, user_id: int) -> Dict[str, int]:
    """
    Gibt zurück, wie viele QR-Codes ein Benutzer bereits erstellt hat.
    """
    used_dynamic: int = (
        db.query(QRCode)
        .filter(QRCode.user_id == user_id, QRCode.is_dynamic == True)
        .count()
    )
    used_static: int = (
        db.query(QRCode)
        .filter(QRCode.user_id == user_id, QRCode.is_dynamic == False)
        .count()
    )

    return {
        "used_dynamic": used_dynamic,
        "used_static": used_static,
        "total": used_dynamic + used_static,
    }


def can_create_dynamic(user: Optional[Dict[str, str]], db: Session) -> Tuple[bool, int, int]:
    """
    Prüft, ob der Benutzer noch einen dynamischen QR-Code erstellen darf.
    Gibt zurück:
      (darf_erstellen, aktuell_verwendet, limit)
    """
    if not user:
        return (False, 0, 0)

    try:
        user_id: int = int(user.get("id", 0))
    except ValueError:
        user_id = 0

    plan: str = (user.get("plan") or "free").lower()
    limit: int = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    used: int = (
        db.query(QRCode)
        .filter(QRCode.user_id == user_id, QRCode.is_dynamic == True)
        .count()
    )

    can_create: bool = used < limit
    return (can_create, used, limit)


# --------------------------------------------------------------------------- #
# 🚀 FastAPI-Route
# --------------------------------------------------------------------------- #

@router.get("/", summary="Zeigt das aktuelle Quota eines Benutzers")
def quota(user_id: int, db: Session = Depends(get_db)) -> Dict[str, int]:
    """
    Gibt das aktuelle Kontingent (Quota) eines Benutzers zurück.
    """
    return get_user_quota_internal(db, user_id)