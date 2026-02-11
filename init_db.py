# =============================================================================
# 🧩 init_db.py
# -----------------------------------------------------------------------------
# Initialisiert die MySQL-Datenbank für Ouhud QR:
#   - Erstellt alle Tabellen (User, Plan, QRCode)
#   - Fügt Standard-Tarifpläne ein (Basic, Pro, Business)
#   - Optional: Erstellt einen Admin-Benutzer
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from database import Base, engine, SessionLocal
from models.user import User
from models.plan import Plan
from models.qrcode import QRCode    # ✅ existiert
# from models.vcard import VCard    # ❌ entfernen – Modell existiert nicht

from passlib.hash import bcrypt

# 🔹 Schritt 1 – Tabellen anlegen
print("🛠️ Erstelle Tabellen in der Datenbank...")
Base.metadata.create_all(bind=engine)
print("✅ Tabellen wurden erfolgreich erstellt.\n")

# 🔹 Schritt 2 – Standard-Daten einfügen
db = SessionLocal()

# === Standardtarife prüfen / einfügen ===
plans_data = [
    {
        "name": "Basic",
        "qr_limit": 10,
        "price": 0.00,
        "has_api_access": False,
        "free_months": 1,
        "description": "Für Einsteiger mit bis zu 10 QR-Codes"
    },
    {
        "name": "Pro",
        "qr_limit": 50,
        "price": 14.99,
        "has_api_access": False,
        "free_months": 0,
        "description": "Erweiterter Plan mit Logo-Optionen und Design-Vorlagen"
    },
    {
        "name": "Business",
        "qr_limit": 250,
        "price": 29.99,
        "has_api_access": True,
        "free_months": 0,
        "description": "Für Unternehmen mit API-Zugang und Verwaltungstools"
    }
]

print("📦 Füge Standard-Tarifpläne hinzu (falls nicht vorhanden)...")
for data in plans_data:
    existing = db.query(Plan).filter(Plan.name == data["name"]).first()
    if not existing:
        new_plan = Plan(**data)
        db.add(new_plan)
        print(f"  ➕ Plan '{data['name']}' hinzugefügt.")
    else:
        print(f"  ✔️ Plan '{data['name']}' bereits vorhanden.")

db.commit()
print("✅ Tarifpläne überprüft und eingefügt.\n")

# === Optional: Admin-Benutzer prüfen / anlegen ===
print("👤 Prüfe auf Admin-Benutzer...")

admin_email = "admin@ouhud.com"
existing_admin = db.query(User).filter(User.email == admin_email).first()

if not existing_admin:
    admin_user = User(
        username="admin",
        first_name="System",
        last_name="Administrator",
        email=admin_email,
        email_verified=True,
        password_hash=bcrypt.hash("admin123"),
        plan_id=1  # Basic als Standard
    )
    db.add(admin_user)
    db.commit()
    print(f"  🆕 Admin-Benutzer erstellt: {admin_email} / Passwort: admin123")
else:
    print("  ✔️ Admin-Benutzer existiert bereits.")

db.close()
print("\n🎉 Datenbankinitialisierung abgeschlossen!")