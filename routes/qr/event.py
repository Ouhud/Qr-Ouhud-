# routes/qr/event.py
# =============================================================================
# 🚀 Event/Calendar QR-Code Routes (Ouhud QR)
# =============================================================================

from __future__ import annotations
import os
import uuid
import base64
from datetime import datetime
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

router = APIRouter(prefix="/qr/event", tags=["Event QR"])

templates = Jinja2Templates(directory="templates")

QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


def _build_dynamic_url(request: Request, slug: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"


def _split_datetime_local(value: str) -> tuple[str, str]:
    if not value:
        return "", ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        if "T" in value:
            date_part, time_part = value.split("T", 1)
            return date_part, time_part[:5]
        return value, ""


def _ics_datetime(date_str: str, time_str: str) -> str:
    if not date_str:
        return ""
    compact_date = date_str.replace("-", "")
    compact_time = (time_str or "00:00").replace(":", "")
    if len(compact_time) == 4:
        compact_time = f"{compact_time}00"
    return f"{compact_date}T{compact_time}"


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    """Zeigt das Event QR-Formular."""
    return templates.TemplateResponse("qr_event.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def create_event_qr(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    start: Optional[str] = Form(None),
    end: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    start_time: str = Form(""),
    end_date: Optional[str] = Form(None),
    end_time: str = Form(""),
    dynamicQR: Optional[str] = Form(None),
    style: str = Form("modern"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen Event QR-Code (iCal Format)."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "event_logo")
    
    # Datum/Zeit aus datetime-local oder Fallback-Feldern auflösen
    if start:
        start_date, start_time = _split_datetime_local(start)
    if end:
        end_date, end_time = _split_datetime_local(end)
    if not start_date:
        raise HTTPException(status_code=422, detail="Startdatum fehlt")

    dtstart = _ics_datetime(start_date, start_time)
    dtend = _ics_datetime(end_date or "", end_time)
    
    # iCal Text generieren
    ics_text = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Ouhud QR//EN\n"
        "BEGIN:VEVENT\n"
        f"SUMMARY:{title}\n"
    )
    if dtstart:
        ics_text += f"DTSTART:{dtstart}\n"
    if dtend:
        ics_text += f"DTEND:{dtend}\n"
    if location:
        ics_text += f"LOCATION:{location}\n"
    if description:
        ics_text += f"DESCRIPTION:{description}\n"
    ics_text += "END:VEVENT\nEND:VCALENDAR\n"
    
    # Dynamik-Option aus Formular (Checkbox)
    is_dynamic = dynamicQR is not None and str(dynamicQR).lower() not in {"0", "false", "off", "no"}
    dynamic_url = _build_dynamic_url(request, slug) if is_dynamic else None

    # QR-Code generieren (dynamisch = /d/{slug}, statisch = iCal-Inhalt direkt)
    payload = dynamic_url or ics_text
    
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
    qr_file = QR_DIR / f"event_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # In DB speichern
    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="event",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        is_dynamic=is_dynamic,
        logo_path=logo_public_path,
        style=style,
        title=title,
    )
    qr.set_data(
        {
            "ics": ics_text,
            "title": title,
            "description": description,
            "location": location,
            "start_date": start_date,
            "start_time": start_time,
            "end_date": end_date,
            "end_time": end_time,
            "is_dynamic": is_dynamic,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    # Base64 für Preview
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    
    return templates.TemplateResponse(
        "qr_event_result.html",
        {"request": request, "qr": qr, "qr_image": qr_base64, "dynamic_url": dynamic_url, "ics": ics_text},
    )
