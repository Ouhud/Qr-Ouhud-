from __future__ import annotations
import os
import json
import logging
from typing import Any, Dict, Optional, Union, cast
from mysql.connector import pooling, Error, MySQLConnection
from mysql.connector.pooling import PooledMySQLConnection
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# ⚙️ ENV laden
# --------------------------------------------------------------------------- #
load_dotenv()

MYSQL_CONFIG: Dict[str, Any] = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASS", ""),
    "database": os.getenv("MYSQL_DB", "ouhud_qr"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
}

# --------------------------------------------------------------------------- #
# 🔁 Connection Pool erstellen
# --------------------------------------------------------------------------- #
try:
    connection_pool: Optional[pooling.MySQLConnectionPool] = pooling.MySQLConnectionPool(
        pool_name="ouhud_pool",
        pool_size=5,
        pool_reset_session=True,
        **MYSQL_CONFIG,
    )
    logging.info("✅ MySQL Connection Pool erfolgreich initialisiert.")
except Error as e:
    logging.error(f"❌ Fehler beim Erstellen des Connection Pools: {e}")
    connection_pool = None


# --------------------------------------------------------------------------- #
# 🔌 Verbindung holen
# --------------------------------------------------------------------------- #
def get_connection() -> Optional[Union[MySQLConnection, PooledMySQLConnection]]:
    """Holt eine Verbindung aus dem Connection Pool."""
    if not connection_pool:
        raise RuntimeError("❌ Kein aktiver MySQL-Verbindungspool verfügbar.")
    conn = connection_pool.get_connection()
    return cast(Union[MySQLConnection, PooledMySQLConnection], conn)


# --------------------------------------------------------------------------- #
# 🧾 QR-Code einfügen
# --------------------------------------------------------------------------- #
def insert_qr(data: Dict[str, Any]) -> bool:
    """Fügt einen neuen QR-Code in die MySQL-Datenbank ein."""
    conn: Optional[Union[MySQLConnection, PooledMySQLConnection]] = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            raise RuntimeError("Keine Verbindung zur Datenbank.")
        cursor = conn.cursor()

        sql = """
        INSERT INTO qr_codes (user_id, slug, name, type, payload, qr_path, fields, is_dynamic)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            data.get("user_id"),
            data.get("slug"),
            data.get("name"),
            data.get("type"),
            data.get("payload"),
            data.get("qr_path"),
            json.dumps(data.get("fields", {})),
            int(bool(data.get("is_dynamic", False))),
        ))
        conn.commit()
        logging.info(f"✅ Neuer QR-Code eingefügt: {data.get('slug')}")
        return True

    except Error as e:
        logging.error(f"❌ Fehler bei insert_qr: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# --------------------------------------------------------------------------- #
# 🔍 QR-Code abrufen
# --------------------------------------------------------------------------- #
def get_qr_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Holt einen QR-Code anhand seines Slugs."""
    conn: Optional[Union[MySQLConnection, PooledMySQLConnection]] = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            raise RuntimeError("Keine Verbindung zur Datenbank.")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM qr_codes WHERE slug = %s", (slug,))
        result = cursor.fetchone()
        return cast(Optional[Dict[str, Any]], result)

    except Error as e:
        logging.error(f"❌ Fehler bei get_qr_by_slug: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# --------------------------------------------------------------------------- #
# ✏️ QR-Code aktualisieren
# --------------------------------------------------------------------------- #
def update_qr(slug: str, updates: Dict[str, Any]) -> bool:
    """Aktualisiert Felder eines vorhandenen QR-Codes."""
    if not updates:
        logging.warning("⚠️ update_qr wurde ohne Daten aufgerufen.")
        return False

    conn: Optional[Union[MySQLConnection, PooledMySQLConnection]] = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            raise RuntimeError("Keine Verbindung zur Datenbank.")
        cursor = conn.cursor()

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        values = list(updates.values()) + [slug]
        sql = f"UPDATE qr_codes SET {set_clause} WHERE slug = %s"

        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"✅ QR-Code '{slug}' erfolgreich aktualisiert.")
        return True

    except Error as e:
        logging.error(f"❌ Fehler bei update_qr: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# --------------------------------------------------------------------------- #
# 🗑️ QR-Code löschen
# --------------------------------------------------------------------------- #
def delete_qr(slug: str) -> bool:
    """Löscht einen QR-Code anhand seines Slugs."""
    conn: Optional[Union[MySQLConnection, PooledMySQLConnection]] = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            raise RuntimeError("Keine Verbindung zur Datenbank.")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qr_codes WHERE slug = %s", (slug,))
        conn.commit()
        logging.info(f"🗑️ QR-Code '{slug}' gelöscht.")
        return True

    except Error as e:
        logging.error(f"❌ Fehler bei delete_qr: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()