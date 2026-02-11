from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class QRShare(Base):
    __tablename__ = "qr_shares"
    __table_args__ = (UniqueConstraint("qr_id", "user_id", name="uq_qr_share_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    qr_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="viewer")  # admin/editor/viewer
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
