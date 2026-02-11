from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.qrcode import QRCode
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_qr import WorkspaceQR
from models.qr_share import QRShare
from routes.auth import get_current_user

router = APIRouter(prefix="/team", tags=["Team & Access"])
templates = Jinja2Templates(directory="templates")


@router.get("/workspaces", response_class=HTMLResponse)
def list_workspaces(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    owned = db.query(Workspace).filter(Workspace.owner_user_id == user.id).all()
    member_ids = db.query(WorkspaceMember.workspace_id).filter(WorkspaceMember.user_id == user.id).all()
    member_ids = [wid for (wid,) in member_ids]
    member_of = db.query(Workspace).filter(Workspace.id.in_(member_ids)).all() if member_ids else []

    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).all()
    role_map = {m.workspace_id: m.role for m in memberships}

    my_qrs = (
        db.query(QRCode)
        .filter(QRCode.user_id == user.id)
        .order_by(QRCode.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "team_workspaces.html",
        {
            "request": request,
            "owned": owned,
            "member_of": member_of,
            "role_map": role_map,
            "my_qrs": my_qrs,
        },
    )


@router.post("/workspaces/create")
def create_workspace(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ws = Workspace(name=name.strip(), description=description.strip() or None, owner_user_id=user.id)
    db.add(ws)
    db.commit()
    return RedirectResponse("/team/workspaces", status_code=303)


@router.post("/workspaces/{workspace_id}/members/add")
def add_member(
    workspace_id: int,
    email: str = Form(...),
    role: str = Form("viewer"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.owner_user_id == user.id).first()
    if not ws:
        raise HTTPException(403, "Keine Berechtigung")

    target = db.query(User).filter(User.email == email.strip()).first()
    if not target:
        return RedirectResponse(f"/team/workspaces?error=user_not_found", status_code=303)

    role = role if role in {"admin", "editor", "viewer"} else "viewer"
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target.id,
    ).first()
    if existing:
        existing.role = role
    else:
        db.add(WorkspaceMember(workspace_id=workspace_id, user_id=target.id, role=role))

    db.commit()
    return RedirectResponse("/team/workspaces", status_code=303)


@router.post("/workspaces/{workspace_id}/qrs/assign")
def assign_qr(
    workspace_id: int,
    qr_slug: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.owner_user_id == user.id).first()
    if not ws:
        raise HTTPException(403, "Keine Berechtigung")

    qr = db.query(QRCode).filter(QRCode.slug == qr_slug, QRCode.user_id == user.id).first()
    if not qr:
        return RedirectResponse("/team/workspaces?error=qr_not_found", status_code=303)

    existing = db.query(WorkspaceQR).filter(WorkspaceQR.workspace_id == workspace_id, WorkspaceQR.qr_id == qr.id).first()
    if not existing:
        db.add(WorkspaceQR(workspace_id=workspace_id, qr_id=qr.id))
        db.commit()

    return RedirectResponse("/team/workspaces", status_code=303)


@router.post("/share")
def share_qr(
    qr_slug: str = Form(...),
    user_email: str = Form(...),
    role: str = Form("viewer"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    qr = db.query(QRCode).filter(QRCode.slug == qr_slug, QRCode.user_id == user.id).first()
    if not qr:
        return RedirectResponse("/team/workspaces?error=qr_not_found", status_code=303)

    target = db.query(User).filter(User.email == user_email.strip()).first()
    if not target:
        return RedirectResponse("/team/workspaces?error=user_not_found", status_code=303)

    role = role if role in {"admin", "editor", "viewer"} else "viewer"
    existing = db.query(QRShare).filter(QRShare.qr_id == qr.id, QRShare.user_id == target.id).first()
    if existing:
        existing.role = role
    else:
        db.add(QRShare(qr_id=qr.id, user_id=target.id, role=role))

    db.commit()
    return RedirectResponse("/team/workspaces", status_code=303)
