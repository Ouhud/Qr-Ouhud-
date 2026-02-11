from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.qrcode import QRCode
from routes.qr.logo_utils import save_qr_logo
from routes.utils import normalize_url
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/qr/wallet", tags=["Wallet QR"])
templates = Jinja2Templates(directory="templates")
QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


def _build_dynamic_url(request: Request, slug: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("qr_wallet_form.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def generate_wallet_qr(
    request: Request,
    pass_url: str = Form(""),
    apple_pass_url: str = Form(""),
    google_pass_url: str = Form(""),
    wallet_type: str = Form("loyalty"),
    title: str = Form(""),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    if not (pass_url or apple_pass_url or google_pass_url):
        raise HTTPException(status_code=400, detail="Mindestens eine Wallet-URL ist erforderlich")
    slug = uuid.uuid4().hex[:10]
    dynamic_url = _build_dynamic_url(request, slug)
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "wallet_logo")

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
    qr_file = QR_DIR / f"wallet_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)

    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="wallet",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"Wallet: {wallet_type}",
    )
    qr.set_data(
        {
            "pass_url": normalize_url(pass_url) if pass_url else "",
            "apple_pass_url": normalize_url(apple_pass_url) if apple_pass_url else "",
            "google_pass_url": normalize_url(google_pass_url) if google_pass_url else "",
            "wallet_type": wallet_type,
            "title": title,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)

    qr_image = base64.b64encode(qr_bytes).decode("utf-8")
    return templates.TemplateResponse(
        "qr_wallet_result.html",
        {"request": request, "qr": qr, "qr_image": qr_image, "dynamic_url": dynamic_url},
    )
