# routes/qr/url.py
# =============================================================================
# 🚀 URL QR-Code Routes (Ouhud QR)
# 🔐 Alle Inhalte werden AES-256-GCM verschlüsselt für Privatschutz
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
from routes.auth import get_current_user
from routes.qr.logo_utils import save_qr_logo
from utils.access_control import can_edit_qr
from utils.qr_generator import generate_qr_png
from utils.qr_config import get_qr_style

router = APIRouter(prefix="/qr/url", tags=["URL QR"])

templates = Jinja2Templates(directory="templates")

QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    """Zeigt das URL QR-Formular."""
    return templates.TemplateResponse("qr_url.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def create_url_qr(
    request: Request,
    url: str = Form(...),
    name: str = Form(...),
    style: str = Form("ouhud"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen URL QR-Code."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "url_logo")
    
    # Dynamische URL für den QR-Code
    dynamic_url = f"https://ouhud.com/d/{slug}"
    
    # QR-Code generieren
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
    qr_file = QR_DIR / f"url_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # Temporäres QR-Objekt erstellen um Daten zu verschlüsseln
    temp_qr = QRCode()
    temp_qr.set_data({"url": url, "name": name, "logo_path": logo_public_path})
    encrypted_content = temp_qr.encrypted_content
    
    # In DB speichern
    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="url",
        encrypted_content=encrypted_content,  # 🔐 Verschlüsselt
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=name,
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    # Base64 für Preview
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    
    return templates.TemplateResponse(
        "qr_url_result.html",
        {
            "request": request,
            "qr": qr,
            "qr_image": qr_base64,
            "dynamic_url": dynamic_url,
            "target_url": url,
        },
    )


@router.get("/edit/{qr_id}", response_class=HTMLResponse)
def edit_qr(
    request: Request,
    qr_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> HTMLResponse:
    """Zeigt das Bearbeitungsformular für einen URL QR-Code."""
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(404, "QR nicht gefunden")
    if not can_edit_qr(db, user.id, qr):
        raise HTTPException(403, "Keine Berechtigung")
    return templates.TemplateResponse("qr_url.html", {"request": request, "qr": qr})


@router.post("/update/{qr_id}", response_class=HTMLResponse)
async def update_url_qr(
    request: Request,
    qr_id: int,
    url: str = Form(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> HTMLResponse:
    """
    Aktualisiert den Ziel-URL eines dynamischen QR-Codes.
    Das QR-Bild bleibt UNVERÄNDERT - es zeigt immer auf /d/{slug}
    🔐 Daten werden verschlüsselt gespeichert.
    """
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(404, "QR nicht gefunden")
    if not can_edit_qr(db, user.id, qr):
        raise HTTPException(403, "Keine Berechtigung")
    
    # Daten verschlüsselt speichern
    qr.set_data({"url": url, "title": title})  # 🔐 Verschlüsselt
    qr.title = title
    
    db.commit()
    db.refresh(qr)
    
    # Zeige das bestehende QR-Bild
    return templates.TemplateResponse(
        "qr_url_result.html",
        {
            "request": request, 
            "qr": qr, 
            "dynamic_url": qr.dynamic_url,
            "target_url": url,
            "message": "✅ Ziel-URL wurde aktualisiert! Das QR-Bild bleibt gleich."
        },
    )


@router.get("/v/{slug}", response_class=HTMLResponse)
def view_url(request: Request, slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Zeigt die aufgelöste URL an."""
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "url").first()
    if not qr:
        raise HTTPException(404, "QR nicht gefunden")
    
    # Daten entschlüsselt abrufen
    content = qr.get_data() or {}  # 🔐 Automatisch entschlüsselt
    target_url = content.get("url", "")
    
    return templates.TemplateResponse(
        "qr_url_dynamic.html",
        {"request": request, "qr": qr, "target_url": target_url},
    )
