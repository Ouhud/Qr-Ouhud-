from __future__ import annotations

import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.link_health_check import LinkHealthCheck
from models.qrcode import QRCode
from routes.auth import get_current_user

router = APIRouter(prefix="/sla", tags=["SLA Monitoring"])
templates = Jinja2Templates(directory="templates")


URL_KEYS = ["url", "review_url", "booking_url", "product_url", "payment_url", "pass_url", "gs1_link"]


def _target_from_qr(qr: QRCode) -> Optional[str]:
    data = qr.get_data() or {}
    for k in URL_KEYS:
        val = data.get(k)
        if isinstance(val, str) and val.startswith("http"):
            return val
    return None


@router.post("/check")
def run_checks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    qrs = db.query(QRCode).filter(QRCode.user_id == user.id, QRCode.active == True).all()
    checked = 0
    with httpx.Client(timeout=8.0, follow_redirects=True) as client:
        for qr in qrs:
            target = _target_from_qr(qr)
            if not target:
                continue
            checked += 1
            start = time.perf_counter()
            status_code = None
            ok = False
            err = None
            try:
                resp = client.get(target)
                status_code = resp.status_code
                ok = 200 <= resp.status_code < 400
            except Exception as exc:
                err = str(exc)[:250]
            elapsed = int((time.perf_counter() - start) * 1000)
            row = LinkHealthCheck(
                qr_id=qr.id,
                target_url=target,
                status_code=status_code,
                response_time_ms=elapsed,
                ok=ok,
                error=err,
            )
            db.add(row)
    db.commit()
    return RedirectResponse(f"/sla/status?checked={checked}", status_code=303)


@router.get("/status", response_class=HTMLResponse)
def status_page(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = (
        db.query(LinkHealthCheck)
        .join(QRCode, QRCode.id == LinkHealthCheck.qr_id)
        .filter(QRCode.user_id == user.id)
        .order_by(LinkHealthCheck.checked_at.desc())
        .limit(100)
        .all()
    )

    avg_latency = db.query(func.avg(LinkHealthCheck.response_time_ms)).join(QRCode, QRCode.id == LinkHealthCheck.qr_id).filter(QRCode.user_id == user.id).scalar()
    ok_count = db.query(func.count(LinkHealthCheck.id)).join(QRCode, QRCode.id == LinkHealthCheck.qr_id).filter(QRCode.user_id == user.id, LinkHealthCheck.ok == True).scalar() or 0
    all_count = db.query(func.count(LinkHealthCheck.id)).join(QRCode, QRCode.id == LinkHealthCheck.qr_id).filter(QRCode.user_id == user.id).scalar() or 0

    uptime = round((ok_count / all_count) * 100, 2) if all_count else 0.0

    return templates.TemplateResponse(
        "sla_status.html",
        {
            "request": request,
            "rows": rows,
            "avg_latency": int(avg_latency or 0),
            "uptime": uptime,
            "checked": request.query_params.get("checked"),
        },
    )
