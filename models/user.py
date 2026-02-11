# =============================================================================
# 👤 models/user.py
# Benutzer-Modell (moderne SQLAlchemy 2.0 Architektur)
# =============================================================================

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.qrcode import QRCode
    from models.plan import Plan


class User(Base):
    __tablename__ = "users"

    # =========================================================================
    # 🧩 Basisinformationen
    # =========================================================================
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str] = mapped_column(String(255))

    # =========================================================================
    # 🖼️ Profil
    # =========================================================================
    profile_image: Mapped[Optional[str]] = mapped_column(String(255))

    # =========================================================================
    # 💼 Tarif / Plan
    # =========================================================================
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plans.id"))
    plan: Mapped[Optional["Plan"]] = relationship(
        "Plan",
        back_populates="users",
        lazy="joined"
    )

    plan_status: Mapped[str] = mapped_column(String(50), default="active")

    plan_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )

    # =========================================================================
    # 📊 Benutzerkontingente
    # =========================================================================
    qr_limit: Mapped[int] = mapped_column(Integer, default=10)

    # =========================================================================
    # 🔐 Sicherheit
    # =========================================================================
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(128))
    api_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True)
    api_key_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # =========================================================================
    # 🕒 Zeitstempel
    # =========================================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # =========================================================================
    # 🔗 Beziehungen
    # =========================================================================
    qrcodes: Mapped[List["QRCode"]] = relationship(
        "QRCode",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # ✅ Kein VCard-Modell mehr – zentraler QR-Ansatz!
    # vcards entfernt.

    # =========================================================================
    # 📌 Representation
    # =========================================================================
    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', verified={self.email_verified}, "
            f"plan_id={self.plan_id}, plan_status='{self.plan_status}')>"
        )
