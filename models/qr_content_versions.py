# models/qr_content_versions.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.mysql import JSON as MyJSON
from datetime import datetime, timezone
from database import Base

class QRContentVersion(Base):
    __tablename__ = "qr_content_versions"
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(Integer, primary_key=True)
    qr_id = Column(Integer, ForeignKey("qr_codes.id", ondelete="CASCADE"), nullable=False)
    qr_type = Column(String(50), nullable=False)  # z. B. 'url', 'vcard', 'wifi', 'product' …
    public_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Hauptinhalt (JSON oder Text)
    content_json = Column(MyJSON().with_variant(Text, "sqlite"), nullable=False)

    # Zusatzinfo zur Änderung
    version_note = Column(String(255), nullable=True)

    # Automatische Zeitstempel
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)