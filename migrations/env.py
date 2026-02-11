# =============================================================================
# ⚙️ Alembic Environment Configuration (Ouhud QR)
# -----------------------------------------------------------------------------
# Lädt .env-Variablen, verbindet sich mit MySQL und registriert alle Modelle.
# Voll kompatibel mit FastAPI + SQLAlchemy 2.x + Python 3.12.
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# ----------------------------------------------m---------------------------
# 🔹 .env-Datei laden
# -------------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------------
# 🔹 Alembic-Konfiguration
# -------------------------------------------------------------------------
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------------
# 🔹 MySQL-Verbindung
# -------------------------------------------------------------------------
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "ouhud_qr")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL.replace("%", "%%"))

# -------------------------------------------------------------------------
# 🔹 Modelle importieren, damit Alembic sie erkennt
# -------------------------------------------------------------------------
from database import Base
from models import (
    User,
    Plan,
    QRCode,
    QRScan,
    QRHistory,
    QRContentVersion
)

target_metadata = Base.metadata

# -------------------------------------------------------------------------
# 🔹 Migration im Offline-Modus
# -------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Führt Migrationen im Offline-Modus aus (z. B. in CI/CD)."""
    url = SQLALCHEMY_DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=False,  # 🧩 verhindert unnötige Änderungen
    )

    with context.begin_transaction():
        context.run_migrations()

# -------------------------------------------------------------------------
# 🔹 Migration im Online-Modus
# -------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Führt Migrationen im Online-Modus aus (lokal oder auf Server)."""
    section = config.get_section(config.config_ini_section) or {}
    assert isinstance(section, dict)

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=False,  # 🧩 nichts an bestehenden Defaults ändern
        )

        with context.begin_transaction():
            context.run_migrations()

# -------------------------------------------------------------------------
# 🔹 Einstiegspunkt
# -------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()