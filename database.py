# =============================================================================
# 🗄️ database.py
# -----------------------------------------------------------------------------
# SQLAlchemy-Datenbankkonfiguration für Ouhud QR
# Unterstützt MySQL + .env + UTC-Awareness + Alembic-Kompatibilität
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy.engine import URL

# 🔹 .env laden (z. B. aus .env-Datei im Projektverzeichnis)
load_dotenv()

# 🔹 MySQL-Parameter aus Umgebungsvariablen
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "Gloria28082022@")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB   = os.getenv("MYSQL_DB", "ouhud_qr")

# 🔹 Passwort sicher escapen (bei Sonderzeichen wie @, #, !, %)
encoded_pass = quote_plus(MYSQL_PASS)

# 🔹 SQLAlchemy-Verbindungs-URL (MySQL + PyMySQL)
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{encoded_pass}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

# 🔹 Engine erstellen
# pool_pre_ping = erkennt automatisch unterbrochene Verbindungen
# pool_recycle = hält MySQL-Verbindungen frisch
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280
)

# 🔹 SessionFactory – erzeugt Session für jede Anfrage
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 🔹 Basisklasse für alle SQLAlchemy-Modelle
Base = declarative_base()


# 🔹 Dependency für FastAPI
def get_db():
    """
    Erstellt eine neue Datenbank-Session pro Anfrage und schließt sie automatisch.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()