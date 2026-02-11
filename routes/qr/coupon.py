from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.coupon_redemption import CouponRedemption
from models.qrcode import QRCode
from routes.qr.logo_utils import save_qr_logo
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/qr/coupon", tags=["Coupon QR"])
templates = Jinja2Templates(directory="templates")
QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


def _build_dynamic_url(request: Request, slug: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"


def _is_expired(expires_at: str) -> bool:
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(expires_at)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp
    except Exception:
        return False


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("qr_coupon_form.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def generate_coupon_qr(
    request: Request,
    code: str = Form(...),
    offer: str = Form(...),
    expires_at: str = Form(""),
    max_redemptions: int = Form(100),
    title: str = Form(""),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    dynamic_url = _build_dynamic_url(request, slug)
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "coupon_logo")

    style_conf = get_qr_style(style)
    result = generate_qr_png(
        payload=dynamic_url,
        size=600,
        fg=style_conf["fg"],
        bg=style_conf["bg"],
        gradient=style_conf.get("gradient"),
        frame_color=style_conf.get("frame_color"),
        module_style=style_conf.get("module_style"),
        eye_style=style_conf.get("eye_style"),
        logo_path=logo_fs_path,
    )
    qr_bytes = result if isinstance(result, bytes) else result.get("bytes", b"")
    qr_file = QR_DIR / f"coupon_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)

    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="coupon",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"Coupon: {code}",
    )
    qr.set_data(
        {
            "code": code.strip(),
            "offer": offer.strip(),
            "expires_at": expires_at.strip(),
            "max_redemptions": max_redemptions,
            "title": title,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)

    qr_image = base64.b64encode(qr_bytes).decode("utf-8")
    return templates.TemplateResponse(
        "qr_coupon_result.html",
        {"request": request, "qr": qr, "qr_image": qr_image, "dynamic_url": dynamic_url},
    )


@router.get("/v/{slug}", response_class=HTMLResponse)
def view_coupon_page(request: Request, slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "coupon").first()
    if not qr:
        raise HTTPException(404, "Coupon-QR nicht gefunden")
    data = qr.get_data() or {}
    redemptions = db.query(CouponRedemption).filter(CouponRedemption.qr_id == qr.id).count()
    expired = _is_expired(data.get("expires_at", ""))
    max_redemptions = int(data.get("max_redemptions", 0) or 0)
    sold_out = max_redemptions > 0 and redemptions >= max_redemptions
    return templates.TemplateResponse(
        "qr_coupon_view.html",
        {
            "request": request,
            "qr": qr,
            "data": data,
            "redemptions": redemptions,
            "expired": expired,
            "sold_out": sold_out,
        },
    )


@router.post("/redeem/{slug}")
def redeem_coupon(
    slug: str,
    name: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "coupon").first()
    if not qr:
        raise HTTPException(404, "Coupon-QR nicht gefunden")
    data = qr.get_data() or {}

    if _is_expired(data.get("expires_at", "")):
        return RedirectResponse(f"/qr/coupon/v/{slug}?error=expired", status_code=303)

    max_redemptions = int(data.get("max_redemptions", 0) or 0)
    current = db.query(CouponRedemption).filter(CouponRedemption.qr_id == qr.id).count()
    if max_redemptions > 0 and current >= max_redemptions:
        return RedirectResponse(f"/qr/coupon/v/{slug}?error=soldout", status_code=303)

    red = CouponRedemption(
        qr_id=qr.id,
        code=data.get("code", ""),
        redeemer_name=name.strip() or None,
        redeemer_email=email.strip() or None,
    )
    db.add(red)
    db.commit()
    return RedirectResponse(f"/qr/coupon/v/{slug}?redeemed=1", status_code=303)
