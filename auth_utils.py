# auth_utils.py
import os
import hashlib
import hmac
import time
from typing import Any, Optional
from fastapi import Request
from supabase import create_client, Client
from dotenv import load_dotenv

# 🔧 Umgebungsvariablen laden
load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret")

SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# ⚙️ Supabase optional initialisieren (nur falls vorhanden)
supabase: Optional["Client"] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase-Client initialisiert.")
    except Exception as e:
        print(f"⚠️ Supabase konnte nicht initialisiert werden: {e}")
else:
    print("ℹ️ Supabase wird nicht verwendet (MySQL-Modus aktiv).")

# ---------------------------------------------------------------------
# 🔐 Passwort-Hash
# ---------------------------------------------------------------------
def password_hash(password: str) -> str:
    """Erzeugt einen sicheren SHA256-Hash für Passwörter."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
# 🔑 Token für Passwort-Reset erzeugen
# ---------------------------------------------------------------------
def make_reset_token(user_id: str, expires_in: int = 3600) -> str:
    """Erzeugt ein zeitlich begrenztes Token für Passwort-Reset."""
    expiry = int(time.time()) + expires_in
    message = f"{user_id}:{expiry}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()
    return f"{user_id}:{expiry}:{signature}"


# ---------------------------------------------------------------------
# ✅ Token validieren
# ---------------------------------------------------------------------
def verify_reset_token(token: str) -> tuple[bool, Optional[str]]:
    """Prüft, ob ein Token gültig oder abgelaufen ist."""
    try:
        user_id, expiry, signature = token.split(":")
        if int(expiry) < time.time():
            return False, None
        expected = hmac.new(
            SECRET_KEY.encode(),
            f"{user_id}:{expiry}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature), user_id
    except Exception:
        return False, None

# ---------------------------------------------------------------------
# 👤 Aktueller Benutzer (aus Session)
# ---------------------------------------------------------------------
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User  # sicherstellen, dass du ein User-Modell hast

def current_user(request: Request, db: Session = Depends(get_db)) -> Optional[dict[str, Any]]:
    """
    Liefert den aktuell eingeloggten Benutzer aus der Session.
    Funktioniert mit MySQL (Standard) oder Supabase, falls aktiviert.
    """
    uid = request.session.get("user_id")
    if not uid:
        return None

    # ✅ Prüfen, ob Supabase aktiv ist
    global supabase
    if supabase:
        try:
            res = supabase.table("users").select("*").eq("id", uid).single().execute()
            return getattr(res, "data", None)
        except Exception as e:
            print(f"⚠️ Supabase-Fehler: {e}")

    # ✅ MySQL-Alternative (lokal)
    user = db.query(User).filter(User.id == uid).first()
    if user:
        return {
            "id": user.id,
            "email": user.email,
            "name": getattr(user, "name", ""),
            "plan": getattr(user, "plan", "free"),
        }

    return None