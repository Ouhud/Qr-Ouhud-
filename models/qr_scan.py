# =============================================================================
# 📊 models/qr_scan.py
# -----------------------------------------------------------------------------
# Enthält das SQLAlchemy-Modell für QR-Code-Scans.
# Jeder Datensatz entspricht einem einzelnen Scan (inkl. Gerät, Zeit, Standort).
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utc_now():
    """Gibt aktuelle UTC-Zeit (timezone-aware, Python 3.12-kompatibel) zurück."""
    return datetime.now(timezone.utc)


class QRScan(Base):
    __tablename__ = "qr_scans"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci"
    }

    # ---------------------------------------------------------------------
    # 🔹 Primär- & Fremdschlüssel
    # ---------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    qr_id = Column(Integer, ForeignKey("qr_codes.id", ondelete="CASCADE"), nullable=False, index=True)

    # ---------------------------------------------------------------------
    # 🔹 Scan-Informationen
    # ---------------------------------------------------------------------
    device = Column(String(50), nullable=True)         # z. B. "iPhone", "Android", "Desktop"
    location = Column(String(100), nullable=True)      # optional: z. B. Stadt oder Land
    user_agent = Column(String(255), nullable=True)    # Browser / App-Info (optional)

    # ---------------------------------------------------------------------
    # 🔹 Zeitstempel (UTC-aware)
    # ---------------------------------------------------------------------
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # ---------------------------------------------------------------------
    # 🔹 Beziehungen
    # ---------------------------------------------------------------------
    qr = relationship("QRCode", back_populates="scans", lazy="joined")

    # ---------------------------------------------------------------------
    # 🔹 Repräsentation (Debugging / Logs)
    # ---------------------------------------------------------------------
    def __repr__(self):
        return (
            f"<QRScan(id={self.id}, qr_id={self.qr_id}, device='{self.device}', "
            f"location='{self.location}', timestamp={self.timestamp})>"
        )