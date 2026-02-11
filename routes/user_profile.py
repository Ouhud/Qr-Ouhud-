import os
import shutil
from datetime import datetime, timezone
from typing import Any
from fastapi import (
    APIRouter, Request, Depends, Form, UploadFile, File
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models.user import User
from models.qrcode import QRCode  # ✅ Wichtig: QR-Codes anzeigen
from models.qr_share import QRShare
from models.workspace_member import WorkspaceMember
from models.workspace_qr import WorkspaceQR
from utils.access_control import get_qr_role

# 📁 Router & Templates
router = APIRouter(tags=["Profile"])
templates = Jinja2Templates(directory="templates")

# 📸 Upload-Verzeichnis
UPLOAD_DIR = "static/uploads"


def _normalize_image_path(path: str | None) -> str:
    if not path:
        return "/static/default-qr.png"
    return path if path.startswith("/") else f"/{path}"


def _build_qr_preview(qr: QRCode) -> str:
    data: dict[str, Any] = qr.get_data() or {}
    qr_type = (qr.type or "").lower()

    if qr_type == "url":
        return data.get("url", "")
    if qr_type == "email":
        return data.get("to") or data.get("mailto", "")
    if qr_type == "sms":
        return data.get("phone") or data.get("sms", "")
    if qr_type == "tel":
        return data.get("phone") or data.get("tel", "")
    if qr_type == "wifi":
        return data.get("ssid", "")
    if qr_type == "vcard":
        first = data.get("first_name", "")
        last = data.get("last_name", "")
        return f"{first} {last}".strip()
    if qr_type == "geo":
        lat = data.get("lat", "")
        lon = data.get("lon", "")
        return f"{lat}, {lon}".strip(", ")
    if qr_type == "event":
        return data.get("summary", "")
    if qr_type == "payment":
        return data.get("payment_url", "")
    if qr_type == "product":
        return data.get("name", "")
    if qr_type == "wallet":
        return data.get("wallet_type", "Wallet Pass")
    if qr_type == "gs1":
        return data.get("gtin") or data.get("gs1_link", "")
    if qr_type == "app_deeplink":
        return data.get("deep_link", "")
    if qr_type == "review":
        return data.get("platform", "Review")
    if qr_type == "booking":
        return data.get("provider", "Booking")
    if qr_type == "lead":
        return data.get("headline", "Lead Formular")
    if qr_type == "feedback":
        return data.get("question", "Feedback")
    if qr_type == "coupon":
        return data.get("code", "Coupon")
    if qr_type == "pdf":
        return "PDF-Datei"
    return qr.title or "Dynamischer QR-Code"


def _build_edit_url(qr: QRCode) -> str:
    qr_type = (qr.type or "").lower()
    if qr_type == "vcard":
        return f"/qr/vcard/edit/{qr.slug}"
    if qr_type == "pdf":
        return f"/qr/pdf/edit/{qr.slug}"
    return f"/qr/edit/{qr.slug}"


def _build_view_url(qr: QRCode) -> str:
    qr_type = (qr.type or "").lower()
    if qr_type == "wifi":
        return f"/qr/wifi/v/{qr.slug}"
    return f"/d/{qr.slug}"

# ─────────────────────────────────────────────
# 📄 PROFIL + QR-CODE-ÜBERSICHT
# ─────────────────────────────────────────────
@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    """
    Zeigt das Profil des aktuell eingeloggten Benutzers + alle erstellten QR-Codes.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse("/auth/login", status_code=303)

    # 🔹 Eigene QR-Codes
    owned_qrs: list[QRCode] = (
        db.query(QRCode)
        .filter(QRCode.user_id == user_id)
        .order_by(QRCode.created_at.desc())
        .all()
    )

    # 🔹 Direkt geteilte QR-Codes
    shared_qr_ids = {
        qr_id
        for (qr_id,) in db.query(QRShare.qr_id).filter(QRShare.user_id == user_id).all()
    }

    # 🔹 Workspace-geteilte QR-Codes
    workspace_ids = {
        ws_id
        for (ws_id,) in db.query(WorkspaceMember.workspace_id).filter(WorkspaceMember.user_id == user_id).all()
    }
    if workspace_ids:
        ws_qr_ids = db.query(WorkspaceQR.qr_id).filter(WorkspaceQR.workspace_id.in_(workspace_ids)).all()
        shared_qr_ids.update(qr_id for (qr_id,) in ws_qr_ids)

    shared_qrs: list[QRCode] = []
    if shared_qr_ids:
        shared_qrs = (
            db.query(QRCode)
            .filter(QRCode.id.in_(shared_qr_ids), QRCode.user_id != user_id)
            .order_by(QRCode.created_at.desc())
            .all()
        )

    qrs = sorted(
        {qr.id: qr for qr in [*owned_qrs, *shared_qrs]}.values(),
        key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    qr_items = [
        {
            "id": qr.id,
            "slug": qr.slug,
            "title": qr.title or "QR-Code",
            "type": qr.type,
            "access_role": get_qr_role(db, user_id, qr) or "viewer",
            "created_at": qr.created_at,
            "image_path": _normalize_image_path(qr.image_path),
            "preview": _build_qr_preview(qr),
            "view_url": _build_view_url(qr),
            "edit_url": _build_edit_url(qr),
        }
        for qr in qrs
    ]

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "qr_items": qr_items,
            "qr_count": len(qr_items),
        },
    )

# ─────────────────────────────────────────────
# 🧩 PROFIL AKTUALISIEREN
# ─────────────────────────────────────────────
@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(""),
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """
    Aktualisiert Benutzerinformationen & Profilbild.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse("/auth/login", status_code=303)

    # 🔄 Textfelder
    user.username = (username or user.username).strip()
    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.email = email.strip()

    # 🖼️ Profilbild speichern
    if file and file.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            print(f"[WARNUNG] Ungültiges Format: {ext}")
            return RedirectResponse("/profile?error=invalid_image", status_code=303)

        filename = f"user_{user_id}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user.profile_image = "/" + path.replace("\\", "/")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/profile?error=duplicate_user", status_code=303)
    print(f"[INFO] Profil aktualisiert: {user.email} (ID={user_id})")

    return RedirectResponse("/profile?success=1", status_code=303)


@router.post("/profile/update-image")
async def update_profile_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Separate Route für reinen Avatar-Upload.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse("/auth/login", status_code=303)

    if not file.filename:
        return RedirectResponse("/profile?error=invalid_image", status_code=303)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return RedirectResponse("/profile?error=invalid_image", status_code=303)

    filename = f"user_{user_id}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.profile_image = "/" + path.replace("\\", "/")
    db.commit()
    return RedirectResponse("/profile?success=1", status_code=303)

# ─────────────────────────────────────────────
# 🗑️ PROFILBILD LÖSCHEN
# ─────────────────────────────────────────────
@router.post("/profile/delete-image")
async def delete_profile_image(request: Request, db: Session = Depends(get_db)):
    """
    Entfernt das Profilbild eines Benutzers (setzt Standardbild zurück).
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    img_path = getattr(user, "profile_image", None)

    if img_path and isinstance(img_path, str):
        file_path = img_path.lstrip("/")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[INFO] Profilbild gelöscht: {file_path}")
            except Exception as e:
                print(f"[WARNUNG] Konnte Profilbild nicht löschen: {e}")

    user.profile_image = "/static/default-avatar.png"
    db.commit()

    print(f"[INFO] Profilbild von Benutzer-ID {user_id} zurückgesetzt.")
    return RedirectResponse("/profile?deleted=1", status_code=303)
