from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.feedback_entry import FeedbackEntry
from models.qrcode import QRCode
from routes.qr.logo_utils import save_qr_logo
from utils.qr_config import get_qr_style
from utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/qr/feedback", tags=["Feedback QR"])
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
    return templates.TemplateResponse("qr_feedback_form.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def generate_feedback_qr(
    request: Request,
    question: str = Form("Wie zufrieden sind Sie?"),
    low_label: str = Form("Sehr unzufrieden"),
    high_label: str = Form("Sehr zufrieden"),
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
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "feedback_logo")

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
    qr_file = QR_DIR / f"feedback_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)

    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="feedback",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=title or "NPS Feedback",
    )
    qr.set_data({"question": question, "low_label": low_label, "high_label": high_label, "title": title, "logo_path": logo_public_path})
    db.add(qr)
    db.commit()
    db.refresh(qr)

    qr_image = base64.b64encode(qr_bytes).decode("utf-8")
    return templates.TemplateResponse(
        "qr_feedback_result.html",
        {"request": request, "qr": qr, "qr_image": qr_image, "dynamic_url": dynamic_url},
    )


@router.get("/v/{slug}", response_class=HTMLResponse)
def view_feedback_page(request: Request, slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "feedback").first()
    if not qr:
        raise HTTPException(404, "Feedback-QR nicht gefunden")
    data = qr.get_data() or {}
    return templates.TemplateResponse("qr_feedback_view.html", {"request": request, "qr": qr, "data": data})


@router.post("/submit/{slug}")
def submit_feedback(
    slug: str,
    score: int = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    qr = db.query(QRCode).filter(QRCode.slug == slug, QRCode.type == "feedback").first()
    if not qr:
        raise HTTPException(404, "Feedback-QR nicht gefunden")
    if score < 1 or score > 10:
        raise HTTPException(400, "Score muss zwischen 1 und 10 liegen")

    fb = FeedbackEntry(qr_id=qr.id, score=score, comment=comment.strip() or None, source="qr")
    db.add(fb)
    db.commit()
    return RedirectResponse(f"/qr/feedback/v/{slug}?submitted=1", status_code=303)
