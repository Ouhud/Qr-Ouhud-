# =============================================================================
# 🌍 seeds/plans_seed.py
# -----------------------------------------------------------------------------
# Initialisiert die Standard-Tarifpläne (Plans) für das Ouhud QR-System.
# Wird einmalig ausgeführt, um die Tarife in die MySQL-Datenbank zu schreiben.
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from database import SessionLocal
from models.plan import Plan
from sqlalchemy.exc import SQLAlchemyError

def seed_plans():
    """Erstellt Standardtarife, falls noch keine vorhanden sind."""
    db = SessionLocal()
    try:
        count = db.query(Plan).count()
        if count == 0:
            plans = [
                Plan(
                    name="Basic",
                    qr_limit=10,
                    price=4.99,
                    free_months=1,
                    has_api_access=False,
                    description="Bis zu 10 QR-Codes, ideal für Einsteiger."
                ),
                Plan(
                    name="Pro",
                    qr_limit=50,
                    price=14.99,
                    free_months=3,
                    has_api_access=False,
                    description="Bis zu 50 QR-Codes, Logo & Design-Optionen."
                ),
                Plan(
                    name="Business",
                    qr_limit=250,
                    price=29.99,
                    free_months=6,
                    has_api_access=True,
                    description="250 QR-Codes, inkl. API-Zugang auf Anfrage."
                ),
                Plan(
                    name="Enterprise",
                    qr_limit=999999,
                    price=0.00,
                    free_months=0,
                    has_api_access=True,
                    description="Unbegrenzte Nutzung und API-Zugang auf Anfrage."
                ),
            ]
            db.add_all(plans)
            db.commit()
            print("✅ Tarife erfolgreich initialisiert.")
        else:
            print(f"ℹ️ Es existieren bereits {count} Tarife in der Datenbank.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Fehler beim Initialisieren der Tarife: {e}")
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 🏁 Direkter Startpunkt
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starte Tarif-Initialisierung ...")
    seed_plans()
    print("🏁 Fertig.")