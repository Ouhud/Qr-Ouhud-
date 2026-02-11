#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_check.py — Schema Diagnostics for Ouhud QR

Vergleicht SQLAlchemy-Modelle mit der realen MySQL-Datenbank
und zeigt Unterschiede bei Tabellen, Spalten, Typen, NULL usw.
"""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import (
    String, Integer, Float, Boolean, DateTime, Text as SqlText
)

# -------------------------------------------------------
# 🔹 Pfad und Base importieren
# -------------------------------------------------------
sys.path.append(os.path.abspath("."))
from database import Base   # type: ignore
import models               # type: ignore


# -------------------------------------------------------
# 🔹 DB-URL aus .env
# -------------------------------------------------------
def load_url() -> str:
    load_dotenv()
    user = os.getenv("MYSQL_USER", "root")
    pw = os.getenv("MYSQL_PASS", "")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DB", "ouhud_qr")
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}"


# -------------------------------------------------------
# 🔹 SQLAlchemy-Typen vereinfachen
# -------------------------------------------------------
def simplify_sqla_type(coltype: Any) -> str:
    """Liefert eine einfache Typ-Bezeichnung für SQLAlchemy-Spalten."""
    t = type(coltype)
    if issubclass(t, String):
        return "STRING"
    if issubclass(t, SqlText):
        return "TEXT"
    if issubclass(t, Integer):
        return "INTEGER"
    if issubclass(t, Float):
        return "FLOAT"
    if issubclass(t, Boolean):
        return "BOOLEAN"
    if issubclass(t, DateTime):
        return "DATETIME"
    return t.__name__.upper()


def simplify_mysql_type(dbtype: str) -> str:
    dbtype = dbtype.lower()
    if any(x in dbtype for x in ["varchar", "char", "varbinary"]):
        return "STRING"
    if "text" in dbtype:
        return "TEXT"
    if any(x in dbtype for x in ["int", "tinyint", "smallint", "bigint"]):
        return "INTEGER"
    if any(x in dbtype for x in ["float", "double", "decimal"]):
        return "FLOAT"
    if "datetime" in dbtype or "timestamp" in dbtype:
        return "DATETIME"
    if "bool" in dbtype:
        return "BOOLEAN"
    return dbtype.upper()


# -------------------------------------------------------
# 🔹 Spalten aus MySQL laden
# -------------------------------------------------------
def fetch_mysql_columns(engine: Engine, table: str) -> Dict[str, Dict[str, Any]]:
    """Liest Metadaten (Name, Typ, NULL, Keys) aus information_schema."""
    sql = text("""
        SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_TYPE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = :t
        ORDER BY ORDINAL_POSITION
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"t": table}).mappings().all()
    cols: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        cols[r["COLUMN_NAME"]] = {
            "nullable": (r["IS_NULLABLE"] == "YES"),
            "type": r["COLUMN_TYPE"],
            "key": r["COLUMN_KEY"],
            "default": r["COLUMN_DEFAULT"],
            "extra": r["EXTRA"],
        }
    return cols


# -------------------------------------------------------
# 🔹 Hauptprüfung
# -------------------------------------------------------
def main() -> int:
    url = load_url()
    engine = create_engine(url, future=True)
    insp = inspect(engine)

    model_tables = {t.name: t for t in Base.metadata.sorted_tables}
    model_table_names = set(model_tables.keys())
    db_table_names = set(insp.get_table_names())

    print(f"\n=== 🧭 Verbunden mit: {url.replace(os.getenv('MYSQL_PASS',''), '****')}")
    print("\n=== 🗂️ Tabellenübersicht ===")
    print("✅ Vorhanden:", len(model_table_names & db_table_names))
    print("❌ Fehlend:", model_table_names - db_table_names)
    print("❓ Extra:", db_table_names - model_table_names)

    problems = 0
    for tname in sorted(model_table_names & db_table_names):
        sqla_cols = {c.name: c for c in model_tables[tname].columns}
        db_cols = fetch_mysql_columns(engine, tname)

        m_only = set(sqla_cols.keys()) - set(db_cols.keys())
        d_only = set(db_cols.keys()) - set(sqla_cols.keys())
        if m_only or d_only:
            problems += 1
            print(f"\n⚠ {tname}: Spaltenabweichungen")
            if m_only:
                print("   Fehlend in DB:", m_only)
            if d_only:
                print("   Nur in DB:", d_only)

        for cname, c in sqla_cols.items():
            if cname not in db_cols:
                continue
            dbci = db_cols[cname]
            want_type = simplify_sqla_type(c.type)
            have_type = simplify_mysql_type(dbci["type"])
            want_null = bool(c.nullable)
            have_null = bool(dbci["nullable"])
            diffs = []
            if want_type != have_type:
                diffs.append(f"Typ {have_type}->{want_type}")
            if want_null != have_null:
                diffs.append(f"NULL {have_null}->{want_null}")
            if diffs:
                problems += 1
                print(f"   ~ {tname}.{cname}: {', '.join(diffs)}")

    print("\n=== ✅ Ergebnis ===")
    if problems == 0:
        print("Alles passt! DB und Modelle sind synchron.")
    else:
        print(f"{problems} potenzielle Unterschiede gefunden.")
    return problems


if __name__ == "__main__":
    sys.exit(main())