# routes/qr/payment.py
# =============================================================================
# 🚀 Payment QR-Code Routes (Ouhud QR)
# =============================================================================

from __future__ import annotations
import uuid
import base64
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.qrcode import QRCode
from routes.qr.dynamic_url import build_dynamic_url
from routes.qr.logo_utils import save_qr_logo
from utils.qr_generator import generate_qr_png
from utils.qr_config import get_qr_style

router = APIRouter(prefix="/qr/payment", tags=["Payment QR"])

templates = Jinja2Templates(directory="templates")

QR_DIR = Path("static/generated_qr")
QR_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_amount(value: str) -> str:
    raw = (value or "").strip().replace(",", ".")
    if not raw:
        return ""
    try:
        return f"{float(raw):.2f}"
    except ValueError:
        return ""


def _build_epc_payload(
    recipient: str,
    iban: str,
    amount: str,
    currency: str,
    purpose: str,
) -> str:
    """
    Einfaches EPC/SCT-Format (SEPA-QR-Text).
    """
    clean_iban = re.sub(r"\\s+", "", (iban or "").upper())
    norm_amount = _normalize_amount(amount)
    ccy = (currency or "EUR").upper()
    amount_line = f"{ccy}{norm_amount}" if norm_amount else ""

    lines = [
        "BCD",
        "002",
        "1",
        "SCT",
        "",  # BIC optional
        (recipient or "").strip(),
        clean_iban,
        amount_line,
        "",  # Purpose Code optional
        (purpose or "").strip(),
        "",  # Ref optional
    ]
    return "\n".join(lines)


@router.get("/", response_class=HTMLResponse)
def show_form(request: Request) -> HTMLResponse:
    """Zeigt das Payment QR-Formular."""
    return templates.TemplateResponse("qr_payment.html", {"request": request})


@router.post("/generate", response_class=HTMLResponse)
async def create_payment_qr(
    request: Request,
    payment_url: str = Form(""),
    title: str = Form(""),
    description: str = Form(""),
    amount: str = Form(""),
    currency: str = Form("EUR"),
    recipient: str = Form(""),
    iban: str = Form(""),
    purpose: str = Form(""),
    style: str = Form("ouhud"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Erstellt einen Payment QR-Code."""
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    slug = uuid.uuid4().hex[:10]
    logo_fs_path, logo_public_path = save_qr_logo(logo, slug, "payment_logo")
    
    payment_url = (payment_url or "").strip()
    recipient = (recipient or "").strip()
    iban = (iban or "").strip()
    purpose = (purpose or "").strip()
    norm_amount = _normalize_amount(amount)

    # Wenn kein Payment-Link vorhanden ist, versuche EPC-Daten zu bauen
    epc_payload = ""
    if not payment_url and recipient and iban:
        epc_payload = _build_epc_payload(recipient, iban, norm_amount, currency, purpose)

    if not payment_url and not epc_payload:
        raise HTTPException(
            status_code=400,
            detail="Bitte entweder eine Payment-URL oder Empfänger + IBAN angeben.",
        )

    # Dynamische URL
    dynamic_url = build_dynamic_url(request, slug)
    
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
    qr_file = QR_DIR / f"payment_{slug}.png"
    with open(qr_file, "wb") as f:
        f.write(qr_bytes)
    
    # In DB speichern
    display_title = (title or "").strip() or (f"SEPA Zahlung: {recipient}" if recipient else "Payment")

    qr = QRCode(
        user_id=user_id,
        slug=slug,
        type="payment",
        dynamic_url=dynamic_url,
        image_path=str(qr_file),
        logo_path=logo_public_path,
        style=style,
        title=display_title,
    )
    qr.set_data(
        {
            "payment_url": payment_url,
            "recipient": recipient,
            "iban": iban,
            "purpose": purpose,
            "epc_payload": epc_payload,
            "title": display_title,
            "description": description,
            "amount": norm_amount,
            "currency": currency,
            "logo_path": logo_public_path,
        }
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    # Base64 für Preview
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")
    
    return templates.TemplateResponse(
        "qr_payment_result.html",
        {"request": request, "qr": qr, "qr_image": qr_base64, "dynamic_url": dynamic_url},
    )
