# =============================================================================
# 📊 Automatische Erstellung eines ER-Diagramms für Ouhud QR
# -----------------------------------------------------------------------------
# Liest .env-Variablen ein und erzeugt das Schema mit graphviz/pydot
# =============================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph
from database import Base
from dotenv import load_dotenv

# 🔹 .env-Datei laden
load_dotenv()

# 🔹 Datenbankverbindung aus .env lesen
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASS = os.getenv("MYSQL_PASS")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB   = os.getenv("MYSQL_DB")

if not all([MYSQL_USER, MYSQL_PASS, MYSQL_DB]):
    raise ValueError("❌ Fehlende Umgebungsvariablen in .env (MYSQL_USER, MYSQL_PASS, MYSQL_DB)")

DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
print(f"📡 Verwende Datenbank: {DB_URL}")

# 🔹 SQLAlchemy Engine erstellen
engine = create_engine(DB_URL)

# 🔹 Diagramm erzeugen
print("🧩 ER-Diagramm wird erstellt ...")

graph = create_schema_graph(
    metadata=Base.metadata,
    show_datatypes=True,     # Datentypen anzeigen
    show_indexes=False,      # Indexe ausblenden
    rankdir="LR",            # Layoutrichtung: Links → Rechts
    concentrate=False,       # Keine Verbindungen zusammenfassen
    engine=engine
)

# 🔹 Ergebnis speichern
output_file = os.path.join(os.getcwd(), "schema_ouhud_qr.png")
graph.write_png(output_file)

print(f"✅ ER-Diagramm erfolgreich erstellt: {output_file}")
