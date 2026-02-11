# =============================================================================
# 🔄 Dynamischer QR-Code-Resolver (Ouhud QR)
# -----------------------------------------------------------------------------
# Eine einzige Route:
#       GET /d/{slug}
#
# Erkennt automatisch:
#   URL / Email / Tel / SMS / WiFi / Geo / vCard / Event / PDF / Social /
#   Product / Payment / Multilink / uvm.
#
# Fehlerfrei, Pylance-kompatibel, FastAPI-optimiert.
# Autor: Ouhud GmbH – Mohamad Hamza Mehmalat
# =============================================================================

from __future__ import annotations
from typing import Union, Optional, Dict, Any

import os
import json
import random
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import (
    RedirectResponse,
    FileResponse,
    PlainTextResponse,
    HTMLResponse,
)
from sqlalchemy.orm import Session

from database import get_db
from models.qrcode import QRCode
from models.qr_scan import QRScan
from models.qr_conversion import QRConversion

router = APIRouter(tags=["QR-Resolver"])

# ✅ Einheitlicher Rückgabewert (für Editor / Pylance)
ResponseType = Union[
    RedirectResponse,
    FileResponse,
    PlainTextResponse,
    HTMLResponse,
]


def _build_vcard_text(data: Dict[str, Any]) -> str:
    """
    Baut eine vCard aus verschiedenen möglichen Alt-/Neudatenformaten.
    """
    existing = data.get("vcard_text") or data.get("vcard")
    if isinstance(existing, str) and existing.strip():
        return existing

    content = data.get("content")
    if isinstance(content, str) and content.strip().upper().startswith("BEGIN:VCARD"):
        return content

    first_name = data.get("first_name", "") or data.get("name", "")
    last_name = data.get("last_name", "")
    org = data.get("org", "") or data.get("company", "")
    title = data.get("title", "") or data.get("position", "")
    phone = data.get("phone", "")
    email = data.get("email", "")
    website = data.get("website", "")

    fn = f"{first_name} {last_name}".strip() or first_name or last_name
    if not fn and not any([org, phone, email, website]):
        return ""

    vcard_text = (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        f"N:{last_name};{first_name};;;\n"
        f"FN:{fn}\n"
    )
    if org:
        vcard_text += f"ORG:{org}\n"
    if title:
        vcard_text += f"TITLE:{title}\n"
    if phone:
        vcard_text += f"TEL;TYPE=cell:{phone}\n"
    if email:
        vcard_text += f"EMAIL;TYPE=internet:{email}\n"
    if website:
        vcard_text += f"URL:{website}\n"
    vcard_text += "END:VCARD\n"
    return vcard_text


def _device_bucket(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    if "windows" in ua or "macintosh" in ua or "linux" in ua:
        return "desktop"
    return "other"


TEST_IPS = {"127.0.0.1", "::1", "localhost"}


def _is_test_user_agent(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    return (
        ua.startswith("curl/")
        or "postmanruntime" in ua
        or "insomnia" in ua
        or "httpie/" in ua
    )


def _should_track_scan(qr: QRCode, request: Request) -> bool:
    force_track = (request.query_params.get("track") or "").lower() in {"1", "true", "yes"}
    if force_track:
        return True

    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    if client_ip in TEST_IPS:
        return False
    if _is_test_user_agent(user_agent):
        return False

    # Eigene Vorschau-Aufrufe des Besitzers nicht als echten Scan zählen
    try:
        session_user_id = request.session.get("user_id")
    except Exception:
        session_user_id = None
    if session_user_id and int(session_user_id) == int(qr.user_id):
        return False

    return True


def _append_utm(url: str, utm: Dict[str, Any], slug: str) -> str:
    if not url or not isinstance(url, str):
        return url
    if not utm:
        return url
    parts = list(urlsplit(url))
    q = dict(parse_qsl(parts[3], keep_blank_values=True))
    for key in ["source", "medium", "campaign", "term", "content"]:
        val = utm.get(key)
        if val:
            q[f"utm_{key}"] = str(val)
    q.setdefault("utm_qr_slug", slug)
    parts[3] = urlencode(q, doseq=True)
    return urlunsplit(parts)


def _rule_matches(rule: Dict[str, Any], request: Request) -> bool:
    # Zeitfenster (UTC, HH:MM)
    now = datetime.now(timezone.utc).strftime("%H:%M")
    from_time = str(rule.get("time_from", "")).strip()
    to_time = str(rule.get("time_to", "")).strip()
    if from_time and to_time and not (from_time <= now <= to_time):
        return False

    # Land: via Header X-Country oder Query ?country=
    req_country = (request.headers.get("x-country") or request.query_params.get("country") or "").upper()
    countries = [str(c).upper() for c in (rule.get("countries") or [])]
    if countries and req_country not in countries:
        return False

    # Sprache: Accept-Language
    lang = (request.headers.get("accept-language") or "").lower()
    langs = [str(l).lower() for l in (rule.get("languages") or [])]
    if langs and not any(l in lang for l in langs):
        return False

    # Gerät
    device = _device_bucket(request.headers.get("user-agent") or "")
    devices = [str(d).lower() for d in (rule.get("devices") or [])]
    if devices and device not in devices:
        return False
    return True


def _pick_ab_target(ab_targets: list[dict[str, Any]]) -> Optional[str]:
    if not ab_targets:
        return None
    urls = []
    weights = []
    for t in ab_targets:
        u = t.get("url")
        if not u:
            continue
        urls.append(str(u))
        weights.append(float(t.get("weight", 1.0) or 1.0))
    if not urls:
        return None
    return random.choices(urls, weights=weights, k=1)[0]


def _resolve_url_target(qr: QRCode, data: Dict[str, Any], request: Request) -> str:
    # 1) Regel-basiert
    rules = data.get("rules") or []
    for rule in rules:
        if isinstance(rule, dict) and _rule_matches(rule, request):
            target = str(rule.get("target_url") or "")
            if target:
                return _append_utm(target, data.get("utm") or {}, qr.slug)

    # 2) A/B-Ziel
    ab_target = _pick_ab_target(data.get("ab_targets") or [])
    if ab_target:
        return _append_utm(ab_target, data.get("utm") or {}, qr.slug)

    # 3) Default
    default_target = data.get("url") or data.get("target_url") or "/"
    return _append_utm(str(default_target), data.get("utm") or {}, qr.slug)


def _track_conversion(db: Session, qr: QRCode, request: Request, event_type: str = "visit") -> None:
    try:
        conv = QRConversion(
            qr_id=qr.id,
            slug=qr.slug,
            event_type=event_type,
            ip_address=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:255],
            meta_json=json.dumps(
                {
                    "country": request.headers.get("x-country") or request.query_params.get("country"),
                    "lang": request.headers.get("accept-language"),
                    "device": _device_bucket(request.headers.get("user-agent") or ""),
                },
                ensure_ascii=False,
            ),
        )
        db.add(conv)
        db.commit()
    except Exception:
        db.rollback()


# =============================================================================
# ✅ EINZIGER Resolver für ALLE dynamischen QR-Codes
# =============================================================================
@router.get("/d/{slug}", response_model=None)
def resolve(slug: str, request: Request, db: Session = Depends(get_db)) -> ResponseType:
    """
    Zentraler Resolver für dynamische QR-Codes.
    Entscheidet anhand des QR-Typs, wie weitergeleitet wird.
    """
    
    # --- QR-Code finden -------------------------------------------------------
    qr: Optional[QRCode] = (
        db.query(QRCode)
        .filter(QRCode.slug == slug, QRCode.active == True)
        .first()
    )

    if not qr:
        raise HTTPException(404, "QR-Code nicht gefunden")

# --- Scan tracking -------------------------------------------------------
    if _should_track_scan(qr, request):
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        scan = QRScan(
            qr_id=qr.id,
            device=user_agent[:50] if user_agent else "unknown",
            location=client_ip,
            user_agent=user_agent[:255] if user_agent else None,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(scan)
        db.commit()

    qr_type = qr.type.lower()
    
    # 🔐 Verschlüsselte Daten entschlüsseln
    data: Dict[str, Any] = qr.get_data() or {}
    if _should_track_scan(qr, request):
        _track_conversion(db, qr, request, event_type="visit")

    # -------------------------------------------------------------------------
    # ✅ URL
    # -------------------------------------------------------------------------
    if qr_type == "url":
        return RedirectResponse(_resolve_url_target(qr, data, request))

    # -------------------------------------------------------------------------
    # ✅ EMAIL
    # -------------------------------------------------------------------------
    if qr_type == "email":
        target = _append_utm(data.get("mailto", "/"), data.get("utm") or {}, qr.slug)
        return RedirectResponse(target)

    # -------------------------------------------------------------------------
    # ✅ TEL
    # -------------------------------------------------------------------------
    if qr_type == "tel":
        return RedirectResponse(data.get("tel"))

    # -------------------------------------------------------------------------
    # ✅ SMS
    # -------------------------------------------------------------------------
    if qr_type == "sms":
        return RedirectResponse(data.get("sms"))

    # -------------------------------------------------------------------------
    # ✅ WIFI
    # -------------------------------------------------------------------------
    if qr_type == "wifi":
        wifi = data.get("wifi", {})
        if not wifi:
            wifi = {
                "encryption": data.get("encryption", "WPA"),
                "ssid": data.get("ssid", ""),
                "password": data.get("password", ""),
            }
        wifi_str = (
            f"WIFI:T:{wifi.get('encryption','WPA')};"
            f"S:{wifi.get('ssid','')};"
            f"P:{wifi.get('password','')};"
            f"H:{str(data.get('hidden', False)).lower()};;"
        )
        return PlainTextResponse(wifi_str)

    # -------------------------------------------------------------------------
    # ✅ GEO
    # -------------------------------------------------------------------------
    if qr_type == "geo":
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            raise HTTPException(400, "Geodaten fehlen")
        return RedirectResponse(f"https://maps.google.com/?q={lat},{lon}")

    # -------------------------------------------------------------------------
    # ✅ VCARD → .vcf-Download
    # -------------------------------------------------------------------------
    if qr_type == "vcard":
        # Standard: professionelle vCard-Ansicht anzeigen
        # Optionaler Download nur mit ?format=vcf oder ?download=1
        fmt = (request.query_params.get("format") or "").lower()
        download = (request.query_params.get("download") or "").lower() in {"1", "true", "yes"}
        if fmt != "vcf" and not download:
            return RedirectResponse(f"/qr/vcard/v/{slug}")

        vcard_text = _build_vcard_text(data)
        if not vcard_text:
            return RedirectResponse(f"/qr/vcard/v/{slug}")

        filename = f"vcard_{slug}.vcf"
        path = f"/tmp/{filename}"

        with open(path, "w", encoding="utf-8") as f:
            f.write(vcard_text)

        return FileResponse(path, filename=filename, media_type="text/vcard")

    # -------------------------------------------------------------------------
    # ✅ EVENT → .ics-Download
    # -------------------------------------------------------------------------
    if qr_type == "event":
        ics = data.get("ics")
        if not ics:
            raise HTTPException(400, "ICS-Inhalt fehlt")

        filename = f"event_{slug}.ics"
        path = f"/tmp/{filename}"

        with open(path, "w", encoding="utf-8") as f:
            f.write(ics)

        return FileResponse(path, filename=filename, media_type="text/calendar")

    # -------------------------------------------------------------------------
    # ✅ PDF → Datei-Download
    # -------------------------------------------------------------------------
    if qr_type == "pdf":
        pdf_path = data.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(404, "PDF wurde nicht gefunden")
        return FileResponse(pdf_path, filename=os.path.basename(pdf_path))

    # -------------------------------------------------------------------------
    # ✅ SOCIAL LINK
    # -------------------------------------------------------------------------
    if qr_type == "social":
        social_html = data.get("public_html")
        if social_html:
            return HTMLResponse(social_html)
        target = data.get("url") or "/"
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ MULTILINK → Public Landing Page
    # -------------------------------------------------------------------------
    if qr_type == "multilink":
        html = data.get("public_html")
        if html:
            return HTMLResponse(html)
        target = data.get("public_url") or data.get("url")
        if target:
            return RedirectResponse(_append_utm(str(target), data.get("utm") or {}, qr.slug))
        return PlainTextResponse("Multilink ist leer")

    # -------------------------------------------------------------------------
    # ✅ PAYMENT
    # -------------------------------------------------------------------------
    if qr_type == "payment":
        target = data.get("payment_url")
        if target:
            return RedirectResponse(_append_utm(str(target), data.get("utm") or {}, qr.slug))
        epc_payload = data.get("epc_payload")
        if epc_payload:
            return PlainTextResponse(str(epc_payload))
        return RedirectResponse("/")

    # -------------------------------------------------------------------------
    # ✅ PRODUCT
    # -------------------------------------------------------------------------
    if qr_type == "product":
        target = data.get("product_url") or "/"
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ WALLET
    # -------------------------------------------------------------------------
    if qr_type == "wallet":
        ua = (request.headers.get("user-agent") or "").lower()
        is_ios = "iphone" in ua or "ipad" in ua or "ipod" in ua
        is_android = "android" in ua

        apple_target = data.get("apple_pass_url", "")
        google_target = data.get("google_pass_url", "")
        fallback_target = data.get("pass_url", "/")

        if is_ios and apple_target:
            target = apple_target
        elif is_android and google_target:
            target = google_target
        else:
            target = fallback_target or apple_target or google_target or "/"
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ GS1 DIGITAL LINK
    # -------------------------------------------------------------------------
    if qr_type == "gs1":
        target = data.get("gs1_link", "/")
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ APP DEEP LINK (mit Store/Web Fallback)
    # -------------------------------------------------------------------------
    if qr_type == "app_deeplink":
        deep_link = data.get("deep_link", "")
        ios_store = data.get("ios_store_url", "")
        android_store = data.get("android_store_url", "")
        web_fallback = data.get("web_fallback_url", "/")

        ua = (request.headers.get("user-agent") or "").lower()
        is_ios = "iphone" in ua or "ipad" in ua
        is_android = "android" in ua

        if not deep_link:
            return RedirectResponse(web_fallback)

        fallback = ios_store if is_ios and ios_store else android_store if is_android and android_store else web_fallback
        html = f"""
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>App öffnen...</title></head>
        <body style="font-family:system-ui;padding:24px">
          <h2>App wird geöffnet...</h2>
          <p>Falls nichts passiert, <a href="{fallback}">hier klicken</a>.</p>
          <script>
            window.location.href = "{deep_link}";
            setTimeout(function(){{ window.location.href = "{fallback}"; }}, 1500);
          </script>
        </body></html>
        """
        return HTMLResponse(html)

    # -------------------------------------------------------------------------
    # ✅ REVIEW
    # -------------------------------------------------------------------------
    if qr_type == "review":
        target = data.get("review_url", "/")
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ BOOKING
    # -------------------------------------------------------------------------
    if qr_type == "booking":
        target = data.get("booking_url", "/")
        return RedirectResponse(_append_utm(target, data.get("utm") or {}, qr.slug))

    # -------------------------------------------------------------------------
    # ✅ LEAD / FEEDBACK / COUPON
    # -------------------------------------------------------------------------
    if qr_type == "lead":
        return RedirectResponse(f"/qr/lead/v/{slug}")
    if qr_type == "feedback":
        return RedirectResponse(f"/qr/feedback/v/{slug}")
    if qr_type == "coupon":
        return RedirectResponse(f"/qr/coupon/v/{slug}")

    # -------------------------------------------------------------------------
    # ✅ FALLBACK
    # -------------------------------------------------------------------------
    return PlainTextResponse(f"QR-Typ '{qr_type}' wird noch nicht unterstützt.")


@router.get("/d/{slug}/convert")
def track_conversion(
    slug: str,
    request: Request,
    event: str = "conversion",
    value: Optional[float] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db),
):
    qr: Optional[QRCode] = db.query(QRCode).filter(QRCode.slug == slug, QRCode.active == True).first()
    if not qr:
        raise HTTPException(404, "QR-Code nicht gefunden")

    conv = QRConversion(
        qr_id=qr.id,
        slug=qr.slug,
        event_type=event,
        value=value,
        currency=currency,
        ip_address=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    db.add(conv)
    db.commit()
    return {"ok": True, "event": event, "slug": slug}
