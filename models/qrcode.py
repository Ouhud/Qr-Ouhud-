# =============================================================================
# 📦 QRCode Model – zentrales, dynamisches QR-Datenmodell (SQLAlchemy 2.0)
# =============================================================================

from __future__ import annotations

import uuid
import json
from typing import Any, Optional, TYPE_CHECKING, Dict, ClassVar

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime,
    ForeignKey, func, event
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON
from database import Base

if TYPE_CHECKING:
    from models.qr_scan import QRScan
    from models.user import User


# =============================================================================
# 🧩 QRCode-Datenmodell
# =============================================================================
class QRCode(Base):
    """
    Zentrales QR-Code Modell.
    Unterstützt alle 13 QR-Typen dynamisch über JSON ('data'),
    plus Themes, Design, Animationen und dynamische Weiterleitungs-URLs.
    
    🔐 SICHERHEIT: Der 'data' Inhalt wird verschlüsselt gespeichert
    in 'encrypted_content' um die Privatsphäre zu schützen.
    """
    __tablename__ = "qr_codes"
    __allow_unmapped__ = True  # Erlaubt nicht gemappte Attribute

    # ---------------------------------------------------------------------
    # 🧾 Basisattribute
    # ---------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)         # url, vcard, wifi, sms, etc.
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: uuid.uuid4().hex[:10],
    )

    # ---------------------------------------------------------------------
    # 🔗 Beziehungen
    # ---------------------------------------------------------------------
    scans: Mapped[list["QRScan"]] = relationship(
        "QRScan",
        back_populates="qr",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship("User", back_populates="qrcodes")

    # ---------------------------------------------------------------------
    # 📄 Inhalt - ALTE VARIANTEN (für Abwärtskompatibilität)
    # ---------------------------------------------------------------------
    # Alte Systeme hatten 'content' – wir behalten es für Kompatibilität.
    content: Mapped[Optional[str]] = mapped_column(Text)

    # ---------------------------------------------------------------------
    # 🔐 NEU: Verschlüsselter Inhalt (PRIVATSCHUTZ)
    # ---------------------------------------------------------------------
    # Das zentrale JSON-Feld für alle 13 QR-Typen - VERSCHLÜSSELT
    encrypted_content: Mapped[Optional[str]] = mapped_column(
        Text,  # Speichert Base64-verschlüsselten String
        nullable=True,
        comment="Verschlüsselter QR-Inhalt (AES-256-GCM)"
    )
    
    # 🔐 Cache für entschlüsselte Daten (nur temporär, nicht in DB)
    _decrypted_data: ClassVar[Optional[Dict[str, Any]]] = None

    # ---------------------------------------------------------------------
    # 🔗 Dynamische URL & Bild
    # ---------------------------------------------------------------------
    dynamic_url: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=True)

    # ---------------------------------------------------------------------
    # 🎨 Design / Themes / Optionen
    # ---------------------------------------------------------------------
    color_fg: Mapped[str] = mapped_column(String(10), default="#000000")
    color_bg: Mapped[str] = mapped_column(String(10), default="#FFFFFF")
    logo_path: Mapped[Optional[str]] = mapped_column(String(255))
    qr_size: Mapped[int] = mapped_column(Integer, default=300)

    style: Mapped[str] = mapped_column(String(50), default="classic")
    theme_name: Mapped[str] = mapped_column(String(50), default="modern-gradient")
    pattern_style: Mapped[str] = mapped_column(String(50), default="dots")
    gradient: Mapped[Optional[str]] = mapped_column(String(255))
    frame_style: Mapped[Optional[str]] = mapped_column(String(50))

    shadow: Mapped[bool] = mapped_column(Boolean, default=False)
    corner_radius: Mapped[int] = mapped_column(Integer, default=0)

    # ---------------------------------------------------------------------
    # 🖼️ Erweiterte Medienunterstützung
    # ---------------------------------------------------------------------
    svg_path: Mapped[Optional[str]] = mapped_column(String(255))
    animated: Mapped[bool] = mapped_column(Boolean, default=False)
    animation_speed: Mapped[int] = mapped_column(Integer, default=1)

    # ---------------------------------------------------------------------
    # 🕒 Zeitstempel
    # ---------------------------------------------------------------------
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # ---------------------------------------------------------------------
    # 🔐 Verschlüsselungs-Methoden
    # ---------------------------------------------------------------------
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Gibt die entschlüsselten QR-Daten zurück.
        Cached das Ergebnis für die aktuelle Instanz.
        """
        if self._decrypted_data is not None:
            return self._decrypted_data
        
        if self.encrypted_content:
            from utils.encryption import decrypt_qr_content
            decrypted = decrypt_qr_content(self.encrypted_content)
            if decrypted is not None:
                self._decrypted_data = decrypted
                return self._decrypted_data
        
        # Fallback: altes unverschlüsseltes data Feld
        if hasattr(self, 'data') and self.data:
            return self.data
        
        # Fallback: altes content Feld (JSON oder String)
        if self.content:
            if isinstance(self.content, dict):
                return self.content
            if isinstance(self.content, str):
                try:
                    return json.loads(self.content)
                except (json.JSONDecodeError, TypeError):
                    return {"content": self.content}
        
        return None
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        Verschlüsselt und speichert die QR-Daten.
        """
        from utils.encryption import encrypt_qr_content
        self.encrypted_content = encrypt_qr_content(data)
        self._decrypted_data = data
        
        # Altes data Feld leeren (veraltet)
        if hasattr(self, 'data'):
            self.data = None
    
    def clear_cache(self) -> None:
        """Löscht den decrypted data Cache."""
        self._decrypted_data = None

    # ---------------------------------------------------------------------
    # 📌 Repräsentation
    # ---------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<QRCode(id={self.id}, type='{self.type}', slug='{self.slug}', "
            f"style='{self.style}', theme='{self.theme_name}', animated={self.animated})>"
        )


# =============================================================================
# ⚙️ Event: Automatische Slug-Erzeugung
# =============================================================================

from sqlalchemy.orm import Mapper
from sqlalchemy.engine import Connection


@event.listens_for(QRCode, "before_insert")  # type: ignore[misc]
def set_unique_slug(mapper: Mapper, connection: Connection, target: Any) -> None:
    """
    Garantiert, dass jeder QR-Code einen gültigen, eindeutigen Slug erhält.
    """
    if not getattr(target, "slug", None):
        target.slug = uuid.uuid4().hex[:10]


# =============================================================================
# ⚙️ Event: Migration von altem 'data' Feld zu 'encrypted_content'
# =============================================================================

@event.listens_for(QRCode, "load")  # type: ignore[misc]
def migrate_data_on_load(target: QRCode, context: Any) -> None:
    """
    Beim Laden: falls encrypted_content leer aber data existiert,
    werden die Daten automatisch verschlüsselt.
    """
    if not target.encrypted_content and hasattr(target, 'data') and target.data:
        from utils.encryption import encrypt_qr_content
        target.encrypted_content = encrypt_qr_content(target.data)
        target.data = None
