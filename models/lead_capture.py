from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class LeadCapture(Base):
    __tablename__ = "lead_captures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    qr_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id", ondelete="CASCADE"), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(120))
    email: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
