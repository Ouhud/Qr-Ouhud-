from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, func, inspect
from sqlalchemy.engine import Engine


def ensure_login_devices_table(engine: Engine) -> None:
    """Erstellt login_devices falls nicht vorhanden (idempotent)."""
    try:
        insp = inspect(engine)
        if "login_devices" in insp.get_table_names():
            return

        metadata = MetaData()
        Table(
            "login_devices",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("user_id", Integer, nullable=False, index=True),
            Column("session_token", String(128), nullable=False, unique=True, index=True),
            Column("device_name", String(100), nullable=False, default="Unbekannt"),
            Column("ip_address", String(64), nullable=True),
            Column("user_agent", String(255), nullable=True),
            Column("active", Boolean, nullable=False, default=True),
            Column("created_at", DateTime(timezone=True), server_default=func.now()),
            Column("last_seen_at", DateTime(timezone=True), server_default=func.now()),
        )
        metadata.create_all(engine, checkfirst=True)
        print("✅ login_devices Tabelle erstellt/geprüft.")
    except Exception as exc:
        print(f"⚠️ Konnte login_devices Tabelle nicht automatisch erstellen: {exc}")
