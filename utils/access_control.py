from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.qr_share import QRShare
from models.workspace_member import WorkspaceMember
from models.workspace_qr import WorkspaceQR
from models.qrcode import QRCode


ROLE_LEVEL = {"viewer": 1, "editor": 2, "admin": 3}


def get_qr_role(db: Session, user_id: int, qr: QRCode) -> Optional[str]:
    if qr.user_id == user_id:
        return "admin"

    share = db.query(QRShare).filter(QRShare.qr_id == qr.id, QRShare.user_id == user_id).first()
    if share:
        return share.role

    mapping = db.query(WorkspaceQR).filter(WorkspaceQR.qr_id == qr.id).all()
    for m in mapping:
        wm = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == m.workspace_id,
            WorkspaceMember.user_id == user_id,
        ).first()
        if wm:
            return wm.role
    return None


def can_view_qr(db: Session, user_id: int, qr: QRCode) -> bool:
    return get_qr_role(db, user_id, qr) is not None


def can_edit_qr(db: Session, user_id: int, qr: QRCode) -> bool:
    role = get_qr_role(db, user_id, qr)
    return role is not None and ROLE_LEVEL.get(role, 0) >= ROLE_LEVEL["editor"]
