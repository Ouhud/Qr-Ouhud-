# routes/qr/tel.py
# =============================================================================
# 🚀 Tel/Phone QR-Code Routes (Ouhud QR)
# =============================================================================

from __future__ import annotations
import os
import uuid
import base64
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.qrcode import QRCode
from routes.qr.logo_utils import save_qr_logo
from utils.qr_generator import generate_qr_png
from utils.qr_config import get_qr_style

router = APIRouter(prefix="/qr/tel", tags=["Tel QR"])

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
    """Zeigt das Tel QR-Formular."""
    return templates.TemplateResponse("qr_tel.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def create_tel_qr(
    request: Request,
    phone: str = Form(...),
    title: str = Form(""),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen Tel QR-Code."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "tel_logo")
    
    # Tel URL erstellen
    tel_url = f"tel:{phone}"
    
    # Dynamische URL
    dynamic_url = _build_dynamic_url(request, slug)
    
    # QR-Code generieren
    payload = dynamic_url
    
    style_conf = get_qr_style(style)
    result = generate_qr_png(
        payload=payload,
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
    
    # Bild speichern
    qr_file = QR_DIR / f"tel_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # Inhalt verschlüsseln
    temp_qr = QRCode()
    temp_qr.set_data({
        "tel": tel_url,
        "phone": phone,
        "title": title,
        "logo_path": logo_public_path,
    })

    # In DB speichern
    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="tel",
        encrypted_content=temp_qr.encrypted_content,
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"Tel: {phone}",
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    # Base64 für Preview
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    
    return templates.TemplateResponse(
        "qr_tel_result.html",
        {
            "request": request,
            "qr": qr,
            "qr_image": qr_base64,
            "dynamic_url": dynamic_url,
            "tel": tel_url,
            "phone": phone,
        },
    )
