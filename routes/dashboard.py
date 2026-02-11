# =============================================================================
# 📊 routes/dashboard.py
# -----------------------------------------------------------------------------
# Dashboard-Routenmodul für eingeloggte Benutzer:
#   • Zeigt persönliche QR-Code-Statistiken
#   • Diagramme (Scans, Typen, Geräte, Nutzung)
#   • Letzte Scans (aktuell Demo, später dynamisch)
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from datetime import date, datetime, timedelta, timezone, time
import calendar

from database import get_db
from models.user import User
from models.qrcode import QRCode
from models.qr_scan import QRScan
from routes.auth import get_current_user  # Für Session-Authentifizierung

# -------------------------------------------------------------------------
# ⚙️ Router & Template Setup
# -------------------------------------------------------------------------
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")
TEST_IPS = {"127.0.0.1", "::1", "localhost"}


def _detect_device_label(scan: QRScan) -> str:
    ua = ((getattr(scan, "user_agent", None) or getattr(scan, "device", "") or "")).lower()
    if not ua:
        return "Andere"
    if "iphone" in ua or "ipad" in ua or "ios" in ua:
        return "iPhone/iPad"
    if "android" in ua:
        return "Android"
    if "windows" in ua or "macintosh" in ua or "mac os" in ua or "linux" in ua:
        return "Desktop"
    if "bot" in ua or "spider" in ua or "crawler" in ua or "curl/" in ua:
        return "Bot/Tool"
    return "Andere"


# -------------------------------------------------------------------------
# 📊 Dashboard-Hauptseite
# -------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Zeigt das Dashboard mit Statistiken, Diagrammen und QR-Code-Übersicht."""

    # 🔒 Sicherheitsprüfung: nur eingeloggte Benutzer
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    # 📦 QR-Codes des aktuellen Benutzers laden
    qr_codes: List[QRCode] = db.query(QRCode).filter(QRCode.user_id == user.id).all()

    range_key = (request.query_params.get("range") or "7d").lower()
    allowed_ranges = {"7d", "30d", "6m"}
    if range_key not in allowed_ranges:
        range_key = "7d"
    include_test = (request.query_params.get("include_test") or "").lower() in {"1", "true", "yes"}

    # 🧮 Basisstatistiken berechnen
    total_qrcodes = len(qr_codes)

    # Echte Scans aus der Datenbank laden
    qr_ids = [qr.id for qr in qr_codes]
    qr_map = {qr.id: qr for qr in qr_codes}
    all_scans: List[QRScan] = []
    total_scans = 0
    scans_today = 0

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    start_today = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end_today = start_today + timedelta(days=1)

    if qr_ids:
        scan_query = db.query(QRScan).filter(QRScan.qr_id.in_(qr_ids))
        if not include_test:
            scan_query = (
                scan_query
                .filter(or_(QRScan.location.is_(None), ~QRScan.location.in_(TEST_IPS)))
                .filter(or_(QRScan.user_agent.is_(None), ~QRScan.user_agent.ilike("curl/%")))
                .filter(or_(QRScan.user_agent.is_(None), ~QRScan.user_agent.ilike("%postmanruntime%")))
                .filter(or_(QRScan.user_agent.is_(None), ~QRScan.user_agent.ilike("%insomnia%")))
                .filter(or_(QRScan.user_agent.is_(None), ~QRScan.user_agent.ilike("%httpie/%")))
            )

        total_scans = (
            scan_query.with_entities(func.count(QRScan.id)).scalar()
            or 0
        )
        scans_today = (
            scan_query.with_entities(func.count(QRScan.id))
            .filter(
                QRScan.timestamp >= start_today,
                QRScan.timestamp < end_today,
            )
            .scalar()
            or 0
        )
        all_scans = scan_query.all()
    
    active_campaigns = len([q for q in qr_codes if q.active])

    # 📂 QR-Code-Aufschlüsselung nach Typ
    stats = {
        "gesamt": total_qrcodes,
        "url": len([q for q in qr_codes if getattr(q, "type", "") == "url"]),
        "vcard": len([q for q in qr_codes if getattr(q, "type", "") == "vcard"]),
        "pdf": len([q for q in qr_codes if getattr(q, "type", "") == "pdf"]),
        "image": len([q for q in qr_codes if getattr(q, "type", "") == "image"]),
        "wifi": len([q for q in qr_codes if getattr(q, "type", "") == "wifi"]),
        "email": len([q for q in qr_codes if getattr(q, "type", "") == "email"]),
        "sms": len([q for q in qr_codes if getattr(q, "type", "") == "sms"]),
    }

    # 📈 Echte Scan-Daten aus der Datenbank (nach Zeitraum)
    chart_labels: list[str] = []
    scans_per_period: list[int] = []
    filtered_scans: list[QRScan] = []
    range_title = "Letzte 7 Tage"

    if range_key == "7d":
        from_date = today - timedelta(days=6)
        start_range = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        filtered_scans = (
            [s for s in all_scans if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp) >= start_range]
        )
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime("%a"))
            scans_per_period.append(
                len([s for s in filtered_scans if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp).date() == d])
            )
        range_title = "Letzte 7 Tage"
    elif range_key == "30d":
        from_date = today - timedelta(days=29)
        start_range = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        filtered_scans = (
            [s for s in all_scans if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp) >= start_range]
        )
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime("%d.%m"))
            scans_per_period.append(
                len([s for s in filtered_scans if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp).date() == d])
            )
        range_title = "Letzte 30 Tage"
    else:  # 6m
        current = today.replace(day=1)
        months: list[tuple[int, int]] = []
        for _ in range(6):
            months.append((current.year, current.month))
            if current.month == 1:
                current = current.replace(year=current.year - 1, month=12)
            else:
                current = current.replace(month=current.month - 1)
        months = list(reversed(months))

        first_year, first_month = months[0]
        from_date = date(first_year, first_month, 1)
        start_range = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        filtered_scans = (
            [s for s in all_scans if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp) >= start_range]
        )
        for y, m in months:
            chart_labels.append(f"{calendar.month_abbr[m]} {str(y)[2:]}")
            scans_per_period.append(
                len(
                    [
                        s
                        for s in filtered_scans
                        if (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp).year == y
                        and (s.timestamp.replace(tzinfo=timezone.utc) if s.timestamp and s.timestamp.tzinfo is None else s.timestamp).month == m
                    ]
                )
            )
        range_title = "Letzte 6 Monate"
    
    # QR-Typ-Verteilung
    qr_type_labels = []
    qr_type_counts = []
    type_stats = {}
    for qr in qr_codes:
        qr_type = getattr(qr, "type", "unknown")
        type_stats[qr_type] = type_stats.get(qr_type, 0) + 1
    
    for qr_type, count in type_stats.items():
        qr_type_labels.append(qr_type.upper())
        qr_type_counts.append(count)
    
    # Geräte-Verteilung aus Scans (im gewählten Zeitraum)
    device_labels = []
    device_counts = []
    device_stats = {}
    for scan in filtered_scans:
        label = _detect_device_label(scan)
        if label == "Bot/Tool":
            continue
        device_stats[label] = device_stats.get(label, 0) + 1

    order = ["iPhone/iPad", "Android", "Desktop", "Andere"]
    for label in order:
        count = device_stats.get(label, 0)
        if count > 0:
            device_labels.append(label)
            device_counts.append(count)

    if not device_labels:
        device_labels = ["Keine Daten"]
        device_counts = [1]

    # ---------------------------------------------------------------------
    # 📦 Tariflimit-Berechnung
    # ---------------------------------------------------------------------
    if total_qrcodes <= 10:
        plan_name = "Basic"
        qr_limit = 10
    elif total_qrcodes <= 50:
        plan_name = "Pro"
        qr_limit = 50
    else:
        plan_name = "Business"
        qr_limit = 250

    qr_usage = total_qrcodes
    qr_remaining = max(qr_limit - qr_usage, 0)

    # 🕒 Letzte Scans (aus gefiltertem Zeitraum)
    recent_scans = []
    for scan in sorted(filtered_scans, key=lambda s: s.timestamp, reverse=True)[:25]:
        qr = qr_map.get(scan.qr_id)
        scan_device = (getattr(scan, "device", "-") or "-").strip()
        if scan_device and len(scan_device) > 32:
            scan_device = scan_device[:32] + "..."
        recent_scans.append({
            "date": scan.timestamp.strftime("%d.%m.%Y %H:%M"),
            "type": getattr(qr, "type", "unknown") if qr else "unknown",
            "location": getattr(scan, "location", "-"),
            "device": scan_device,
            "slug": getattr(qr, "slug", "-") if qr else "-",
        })

    # ---------------------------------------------------------------------
    # 🎨 Template rendern
    # ---------------------------------------------------------------------
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "📊 Ouhud QR – Dashboard",
            "user": user,
            "qr_codes": qr_codes,
            "qr_stats": stats,
            "total_qrcodes": total_qrcodes,
            "total_scans": total_scans,
            "active_campaigns": active_campaigns,
            "scans_today": scans_today,
            "chart_labels": chart_labels,
            "scans_per_period": scans_per_period,
            "range_key": range_key,
            "range_title": range_title,
            "qr_type_labels": qr_type_labels,
            "qr_type_counts": qr_type_counts,
            "device_labels": device_labels,
            "device_counts": device_counts,
            "recent_scans": recent_scans,
            "plan_name": plan_name,
            "qr_limit": qr_limit,
            "qr_usage": qr_usage,
            "qr_remaining": qr_remaining,
        },
    )
