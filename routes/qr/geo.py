# routes/qr/geo.py
# =============================================================================
# 🚀 Geo/Location QR-Code Routes (Ouhud QR)
# =============================================================================

from __future__ import annotations
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

router = APIRouter(prefix="/qr/geo", tags=["Geo QR"])

templates = Jinja2Templates(directory="templates")

QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    """Zeigt das Geo QR-Formular."""
    return templates.TemplateResponse("qr_geo.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def create_geo_qr(
    request: Request,
    latitude: str = Form(...),
    longitude: str = Form(...),
    title: str = Form(""),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen Geo QR-Code."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "geo_logo")
    
    # Geo URL erstellen
    geo_url = f"geo:{latitude},{longitude}"
    
    # Dynamische URL
    dynamic_url = f"https://ouhud.com/d/{slug}"
    
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
    qr_file = QR_DIR / f"geo_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # In DB speichern
    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="geo",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"Geo: {latitude}, {longitude}",
    )
    qr.set_data(
        {
            "geo": geo_url,
            "lat": latitude,
            "lon": longitude,
            "title": title,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    # Base64 für Preview
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    
    return templates.TemplateResponse(
        "qr_geo_result.html",
        {"request": request, "qr": qr, "qr_image": qr_base64, "dynamic_url": dynamic_url, "geo": geo_url},
    )
