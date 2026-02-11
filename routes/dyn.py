from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models.qrcode import QRCode

router = APIRouter(tags=["Legacy Dyn Resolver"])


@router.get("/dyn/{public_id}")
def resolve_legacy(public_id: str, db: Session = Depends(get_db)):
    """
    Legacy-Kompatibilitaet:
    Alte QRs nutzten /dyn/{public_id}. In der aktuellen App laeuft alles ueber /d/{slug}.
    Wir interpretieren den Parameter als slug und leiten auf den zentralen Resolver um.
    """
    qr = (
        db.query(QRCode)
        .filter(QRCode.slug == public_id, QRCode.active == True)
        .first()
    )
    if not qr:
        return HTMLResponse("<h1>❌ QR nicht gefunden</h1>", status_code=404)
    return RedirectResponse(url=f"/d/{qr.slug}", status_code=307)
