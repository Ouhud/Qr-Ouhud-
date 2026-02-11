# =============================================================================
# 📦 models/plan.py
# -----------------------------------------------------------------------------
# Datenmodell für Tarifpläne (Plans) in Ouhud QR.
# Enthält Definitionen für Name, Preis, Limits, kostenlose Monate und API-Zugang.
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base


class Plan(Base):
    """
    Repräsentiert ein Tarifmodell (z. B. Basic, Pro, Business, Enterprise)
    für die Ouhud QR-Plattform.
    """
    __tablename__ = "plans"

    # 🔹 Primärschlüssel
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 🔹 Planname (z. B. Basic, Pro, Business, Enterprise)
    name = Column(String(50), unique=True, nullable=False)

    # 🔹 Maximale Anzahl an QR-Codes, die im Plan erlaubt sind
    qr_limit = Column(Integer, nullable=False)

    # 🔹 Monatlicher Preis in Euro
    price = Column(Float, nullable=False)

    # 🔹 Gibt an, ob API-Zugang enthalten ist
    has_api_access = Column(Boolean, default=False)

    # 🔹 Anzahl der kostenlosen Monate bei Erstregistrierung
    free_months = Column(Integer, default=0)

    # 🔹 Beschreibung (optional, für UI-Anzeige)
    description = Column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # 🔗 Beziehung zu Benutzern
    # -------------------------------------------------------------------------
    users = relationship("User", back_populates="plan")

    # -------------------------------------------------------------------------
    # 🧩 Hilfsmethoden
    # -------------------------------------------------------------------------
    def __repr__(self):
        return (
            f"<Plan(name='{self.name}', "
            f"limit={self.qr_limit}, "
            f"price={self.price:.2f}€, "
            f"free_months={self.free_months}, "
            f"api={self.has_api_access})>"
        )
