# routes/dyn.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.qrcode import QRCode
from models import (
    qr_url, qr_wifi, qr_email, qr_sms, qr_phone,
    qr_social, qr_event, qr_geo, qr_payment, qr_multilink, qr_product
)
import io

router = APIRouter()

@router.get("/dyn/{public_id}")
def resolve(public_id: str, db: Session = Depends(get_db)):
    qr: QRCode | None = db.query(QRCode).filter_by(public_id=public_id).first()
    if not qr:
        return HTMLResponse("<h1>❌ QR nicht gefunden</h1>", status_code=404)

    t = (qr.type or "").lower()

    if t == "url":
        rec = db.query(qr_url.QRUrl).filter_by(qr_id=qr.id).first()
        if not rec or not rec.destination_url:
            return HTMLResponse("Ziel-URL fehlt", status_code=410)
        return RedirectResponse(rec.destination_url, status_code=302)

    if t == "phone":
        rec = db.query(qr_phone.QRPhone).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("Telefonnummer fehlt", status_code=410)
        return RedirectResponse(f"tel:{rec.phone}", status_code=302)

    if t == "sms":
        rec = db.query(qr_sms.QRSMS).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("SMS Ziel fehlt", status_code=410)
        sms_url = f"sms:{rec.phone}"
        # Einige Scanner unterstützen ?&body= – nicht standardisiert.
        return RedirectResponse(sms_url, status_code=302)

    if t == "email":
        rec = db.query(qr_email.QREmail).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("E-Mail-Daten fehlen", status_code=410)
        # mailto: subject/body URL-encoden wenn du möchtest
        return RedirectResponse(f"mailto:{rec.to_email}", status_code=302)

    if t == "wifi":
        rec = db.query(qr_wifi.QRWifi).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("WLAN-Daten fehlen", status_code=410)
        hidden = "true" if rec.hidden else "false"
        wifi_str = f"WIFI:T:{rec.encryption};S:{rec.ssid};P:{rec.password or ''};H:{hidden};;"
        return PlainTextResponse(wifi_str, media_type="text/plain; charset=utf-8")

    if t == "geo":
        rec = db.query(qr_geo.QRGeo).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("Geo-Daten fehlen", status_code=410)
        # deeplink – hängt vom Scanner ab; safer ist eine Karten-URL:
        return RedirectResponse(f"https://maps.google.com/?q={rec.latitude},{rec.longitude}", status_code=302)

    if t == "event":
        rec = db.query(qr_event.QREvent).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("Event-Daten fehlen", status_code=410)
        # ICS generieren
        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Ouhud QR//EN
BEGIN:VEVENT
SUMMARY:{rec.title or ''}
LOCATION:{rec.location or ''}
DTSTART:{rec.start.strftime('%Y%m%dT%H%M%S')}
DTEND:{rec.end.strftime('%Y%m%dT%H%M%S')}
DESCRIPTION:{rec.description or ''}
END:VEVENT
END:VCALENDAR
"""
        return PlainTextResponse(ics, media_type="text/calendar; charset=utf-8")

    if t == "social":
        rec = db.query(qr_social.QRSocial).filter_by(qr_id=qr.id).first()
        if not rec or not rec.url:
            return HTMLResponse("Social-URL fehlt", status_code=410)
        return RedirectResponse(rec.url, status_code=302)

    if t == "payment":
        # Hier könnte man SEPA-QR (EPC) oder PayPal/TWINT-Links generieren
        return HTMLResponse("Payment-Resolver kommt hier hin", status_code=501)

    if t == "multilink":
        rec = db.query(qr_multilink.QRMultiLink).filter_by(qr_id=qr.id).first()
        if not rec:
            return HTMLResponse("MultiLink-Daten fehlen", status_code=410)
        # Eigene schöne HTML-Seite rendern:
        html = f"<h1>{rec.title or 'Links'}</h1>"
        return HTMLResponse(html)

    if t == "product":
        rec = db.query(qr_product.QRProduct).filter_by(public_id=qr.public_id).first()
        if not rec:
            return HTMLResponse("Produkt nicht gefunden", status_code=404)
        # Eigene Template-Seite wäre schöner:
        html = f"<h1>{rec.name}</h1><p>{rec.description or ''}</p>"
        return HTMLResponse(html)

    return HTMLResponse("Unbekannter QR-Typ", status_code=400)