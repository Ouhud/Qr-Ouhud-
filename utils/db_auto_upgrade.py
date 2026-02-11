"""
utils/db_auto_upgrade.py
────────────────────────────────────────────
Automatische Alembic-Migration beim Start der App.
────────────────────────────────────────────
"""

import subprocess
import os

def run_alembic_upgrade():
    """
    Führt "alembic upgrade head" automatisch aus,
    um sicherzustellen, dass DB und Modelle synchron sind.
    """
    print("🔄 Überprüfe Datenbankstruktur ...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Alembic-Migration erfolgreich ausgeführt.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("⚠️ Alembic-Migration fehlgeschlagen!")
        print(e.stderr)
    except FileNotFoundError:
        print("⚠️ Alembic nicht gefunden – bitte pip install alembic prüfen.")

