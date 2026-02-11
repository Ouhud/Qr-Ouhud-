from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class WorkspaceQR(Base):
    __tablename__ = "workspace_qrs"
    __table_args__ = (UniqueConstraint("workspace_id", "qr_id", name="uq_workspace_qr"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    qr_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
