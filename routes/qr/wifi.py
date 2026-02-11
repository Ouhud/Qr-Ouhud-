# routes/qr/wifi.py
# =============================================================================
# 🚀 WiFi QR-Code Routes (Ouhud QR)
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

router = APIRouter(prefix="/qr/wifi", tags=["WiFi QR"])

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
    """Zeigt das WiFi QR-Formular."""
    return templates.TemplateResponse("qr_wifi_form.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def create_wifi_qr(
    request: Request,
    ssid: str = Form(...),
    password: str = Form(...),
    encryption: str = Form("WPA"),
    hidden: bool = Form(False),
    title: str = Form(""),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen WiFi QR-Code."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "wifi_logo")
    
    # WiFi String format: WIFI:T:WPA;S:MyNetwork;P:MyPassword;H:false;;
    # Dynamische URL
    dynamic_url = _build_dynamic_url(request, slug)
    
    # QR-Code generieren (immer dynamisch)
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
    
    # Bild speichern
    qr_file = QR_DIR / f"wifi_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # In DB speichern
    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="wifi",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or f"WLAN: {ssid}",
    )
    qr.set_data(
        {
            "ssid": ssid,
            "password": password,
            "encryption": encryption,
            "hidden": hidden,
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
        "qr_wifi_result.html",
        {"request": request, "qr": qr, "qr_image": qr_base64, "dynamic_url": dynamic_url},
    )


@router.get("/v/{slug}", response_class=HTMLResponse)
def view_wifi_qr(request: Request, slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Zeigt WLAN-Daten lesbar anstatt rohen WIFI-String."""
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "wifi").first()
    if not qr:
        raise HTTPException(404, "WiFi-QR nicht gefunden")
    data = qr.get_data() or {}
    return templates.TemplateResponse(
        "qr_wifi_view.html",
        {"request": request, "qr": qr, "data": data},
    )
