from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    qr_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    redeemer_name: Mapped[Optional[str]] = mapped_column(String(120))
    redeemer_email: Mapped[Optional[str]] = mapped_column(String(200))
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
