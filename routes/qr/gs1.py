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
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/qr/gs1", tags=["GS1 QR"])
templates = Jinja2Templates(directory="templates")
QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


def _build_dynamic_url(request: Request, slug: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"


def _build_gs1_link(base_url: str, gtin: str, batch: str, expiry: str, serial: str) -> str:
    link = f"{base_url.rstrip('/')}/01/{gtin}"
    if batch:
        link += f"/10/{batch}"
    if expiry:
        link += f"/17/{expiry}"
    if serial:
        link += f"/21/{serial}"
    return link


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("qr_gs1_form.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def generate_gs1_qr(
    request: Request,
    base_url: str = Form(...),
    gtin: str = Form(...),
    batch: str = Form(""),
    expiry: str = Form(""),
    serial: str = Form(""),
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
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "gs1_logo")
    gs1_link = _build_gs1_link(base_url, gtin, batch, expiry, serial)

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
    qr_file = QR_DIR / f"gs1_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)

    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="gs1",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"GS1: {gtin}",
    )
    qr.set_data(
        {
            "gs1_link": gs1_link,
            "base_url": base_url,
            "gtin": gtin,
            "batch": batch,
            "expiry": expiry,
            "serial": serial,
            "title": title,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)

    qr_image = base64.b64encode(qr_bytes).decode("utf-8")
    return templates.TemplateResponse(
        "qr_gs1_result.html",
        {"request": request, "qr": qr, "qr_image": qr_image, "dynamic_url": dynamic_url, "gs1_link": gs1_link},
    )
