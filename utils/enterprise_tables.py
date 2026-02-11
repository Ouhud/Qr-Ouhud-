from __future__ import annotations

from sqlalchemy.engine import Engine

from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_qr import WorkspaceQR
from models.qr_share import QRShare
from models.qr_conversion import QRConversion
from models.link_health_check import LinkHealthCheck


def ensure_enterprise_tables(engine: Engine) -> None:
    try:
        Workspace.__table__.create(bind=engine, checkfirst=True)
        WorkspaceMember.__table__.create(bind=engine, checkfirst=True)
        WorkspaceQR.__table__.create(bind=engine, checkfirst=True)
        QRShare.__table__.create(bind=engine, checkfirst=True)
        QRConversion.__table__.create(bind=engine, checkfirst=True)
        LinkHealthCheck.__table__.create(bind=engine, checkfirst=True)
        print("✅ Enterprise-Tabellen geprüft/ergänzt.")
    except Exception as exc:
        print(f"⚠️ Konnte Enterprise-Tabellen nicht automatisch erstellen: {exc}")
