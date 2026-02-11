# models/qr_history.py
from __future__ import annotations

from sqlalchemy import Integer, DateTime, String, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class QRHistory(Base):
    """
    Speichert jede Änderung eines QR-Codes:
    - was wurde geändert?
    - alte Daten
    - neue Daten
    - Zeitpunkt
    - welcher Benutzer
    """
    __tablename__ = "qr_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    qr_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(Integer)

    action: Mapped[str] = mapped_column(String(50))  # "create", "update"
    old_data: Mapped[str] = mapped_column(Text, nullable=True)
    new_data: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    qr = relationship("QRCode")