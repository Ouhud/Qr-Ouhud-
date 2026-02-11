from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.api_key import APIKey
from models.qrcode import QRCode
from models.user import User
from utils.api_keys import hash_api_key
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/api/v1", tags=["Public API"])

QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "url",
    "vcard",
    "pdf",
    "wifi",
    "email",
    "sms",
    "tel",
    "social",
    "event",
    "geo",
    "payment",
    "multilink",
    "product",
    "wallet",
    "gs1",
    "app_deeplink",
    "review",
    "booking",
    "lead",
    "feedback",
    "coupon",
}


class CreateQRIn(BaseModel):
    type: str = Field(..., description="QR type")
    title: str = Field(default="API QR")
    data: dict[str, Any] = Field(default_factory=dict)
    style: str = Field(default="modern")
    active: bool = Field(default=True)


class UpdateQRIn(BaseModel):
    title: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    style: Optional[str] = None
    active: Optional[bool] = None


def _build_dynamic_url(request: Request, slug: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"


def _serialize_qr(qr: QRCode) -> dict[str, Any]:
    return {
        "id": qr.id,
        "slug": qr.slug,
        "type": qr.type,
        "title": qr.title,
        "active": qr.active,
        "dynamic_url": qr.dynamic_url,
        "image_path": qr.image_path,
        "style": qr.style,
        "data": qr.get_data() or {},
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
        "updated_at": qr.updated_at.isoformat() if qr.updated_at else None,
    }


def get_api_user(
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hash_api_key(x_api_key)

    api_key_row = (
        db.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.revoked_at.is_(None))
        .first()
    )
    if api_key_row:
        api_key_row.last_used_at = datetime.now(timezone.utc)
        db.commit()
        user = db.query(User).filter(User.id == api_key_row.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return user

    # Legacy fallback: existing single-key users continue to work
    legacy_user = db.query(User).filter(User.api_key == x_api_key).first()
    if legacy_user:
        return legacy_user

    raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/me")
def me(user=Depends(get_api_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "plan_status": user.plan_status,
    }


@router.get("/qrs")
def list_qrs(
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(get_api_user),
):
    limit = max(1, min(limit, 200))
    rows = (
        db.query(QRCode)
        .filter(QRCode.user_id == user.id)
        .order_by(QRCode.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"items": [_serialize_qr(r) for r in rows], "count": len(rows)}


@router.post("/qrs", status_code=201)
def create_qr(
    payload: CreateQRIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_api_user),
):
    qr_type = payload.type.lower().strip()
    if qr_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported qr type: {qr_type}")

    slug = uuid.uuid4().hex[:10]
    dynamic_url = _build_dynamic_url(request, slug)

    style_conf = get_qr_style(payload.style)
    result = generate_qr_png(
        payload=dynamic_url,
        size=600,
        fg=style_conf["fg"],
        bg=style_conf["bg"],
        gradient=style_conf.get("gradient"),
        frame_color=style_conf.get("frame_color"),
        module_style=style_conf.get("module_style"),
        eye_style=style_conf.get("eye_style"),
    )
    qr_bytes = result if isinstance(result, bytes) else result.get("bytes", b"")
    qr_file = QR_DIR / f"{qr_type}_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)

    qr = QRCode(
        user_id=user.id,
        slug=slug,
        type=qr_type,
        title=payload.title or f"{qr_type.upper()} QR",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        style=payload.style,
        active=payload.active,
    )
    qr.set_data(payload.data or {})
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return _serialize_qr(qr)


@router.get("/qrs/{slug}")
def get_qr(
    slug: str,
    db: Session = Depends(get_db),
    user=Depends(get_api_user),
):
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.user_id == user.id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR not found")
    return _serialize_qr(qr)


@router.patch("/qrs/{slug}")
def update_qr(
    slug: str,
    payload: UpdateQRIn,
    db: Session = Depends(get_db),
    user=Depends(get_api_user),
):
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.user_id == user.id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR not found")

    if payload.title is not None:
        qr.title = payload.title
    if payload.style is not None:
        qr.style = payload.style
    if payload.active is not None:
        qr.active = payload.active
    if payload.data is not None:
        qr.set_data(payload.data)

    db.commit()
    db.refresh(qr)
    return _serialize_qr(qr)


@router.delete("/qrs/{slug}")
def delete_qr(
    slug: str,
    db: Session = Depends(get_db),
    user=Depends(get_api_user),
):
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.user_id == user.id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR not found")
    db.delete(qr)
    db.commit()
    return {"ok": True, "slug": slug}
