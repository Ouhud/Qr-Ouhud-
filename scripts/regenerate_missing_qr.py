#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: regenerate_missing_qr.py
Author: Mohamad Hamza Mehmalat
Project: Ouhud QR
Created: 2025-10-19
Updated: 2025-10-25
Description:
    Dieses Skript überprüft alle QR-Code-Einträge in der MySQL-Datenbank und
    regeneriert fehlende QR-Bilddateien im Verzeichnis 'static/generated_qr'.
"""

import os
import sys
import traceback
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from models.qrcode import QRCode
from typing import Literal, Tuple
# ─────────────────────────────────────────────
# 🧩 Projektpfad einbinden
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# ─────────────────────────────────────────────
# 📦 Interne Importe
# ─────────────────────────────────────────────
from database import SessionLocal
from models.qrcode import QRCode
from utils.qr_generator import generate_qr_png

# ─────────────────────────────────────────────
# 📁 Pfade & Logdatei
# ─────────────────────────────────────────────
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "generated_qr")
LOG_FILE = os.path.join(BASE_DIR, "scripts", "qr_regeneration.log")

# ─────────────────────────────────────────────
# 🎨 Farbige Ausgabe
# ─────────────────────────────────────────────
class Color:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

# ─────────────────────────────────────────────
# 🧩 Logging-Helfer
# ─────────────────────────────────────────────
def log_message(message: str, level: str = "INFO") -> None:
    """Schreibt Nachrichten mit Zeitstempel ins Logfile und farbige Ausgabe in Konsole."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} [{level}] {message}"

    color = {
        "INFO": Color.CYAN,
        "OK": Color.GREEN,
        "WARN": Color.YELLOW,
        "ERROR": Color.RED,
    }.get(level, Color.RESET)

    print(color + line + Color.RESET)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(line + "\n")

# ─────────────────────────────────────────────
# 🔧 Wrapper für generate_qr_png()
# ─────────────────────────────────────────────
def generate_qr_code_compat(
    content: str,
    filename: str,
    color_fg: str = "#000000",
    color_bg: str = "#FFFFFF",
    style: str = "classic",
    size: int = 300,
    logo_path: Optional[str] = None,
) -> None:
    """Wrapper für generate_qr_png(), sorgt für Typkompatibilität."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        result = generate_qr_png(
            payload=content,
            size=int(size),
            fg=color_fg,
            bg=color_bg,
            logo_path=logo_path,
            module_style="square",
            eye_style="square",
            frame_text=None,
            frame_color="#4F46E5",
            gradient=None,
            logo_position="center",
        )

        if isinstance(result, (bytes, bytearray)):
            with open(filename, "wb") as f:
                f.write(result)
        else:
            log_message(f"ℹ️  QR-Code gespeichert (keine Byte-Daten zurückgegeben): {filename}", level="INFO")

    except Exception as e:
        log_message(f"❌ Fehler bei QR-Code {filename}: {e}", level="ERROR")
        traceback.print_exc(file=sys.stdout)
        raise



# ─────────────────────────────────────────────
# 🔄 Regeneration pro QR-Eintrag (typisiert)
# ─────────────────────────────────────────────
def regenerate_single_qr(qr: QRCode) -> Tuple[Literal["skip", "regen", "error"], str]:
    """
    Verarbeitet einen einzelnen QR-Code-Eintrag.

    Parameter:
        qr (QRCode): Ein einzelnes QR-Code-Datenbankobjekt aus der Tabelle `qr_codes`.

    Rückgabe:
        tuple[str, str]: (Status, Dateiname)
            Status ∈ {"skip", "regen", "error"}
            - "skip"  → Datei existiert bereits
            - "regen" → Datei neu generiert
            - "error" → Fehler beim Erstellen
    """
    slug = str(getattr(qr, "slug", ""))
    filename = f"qr_{slug}.png"
    path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(path):
        return "skip", filename

    try:
        log_message(f"⚙️  Erstelle neues QR-Bild: {filename}")
        generate_qr_code_compat(
            content=str(getattr(qr, "content", "")),
            filename=path,
            color_fg=str(getattr(qr, "color_fg", "#000000") or "#000000"),
            color_bg=str(getattr(qr, "color_bg", "#FFFFFF") or "#FFFFFF"),
            style=str(getattr(qr, "style", "classic") or "classic"),
            size=int(getattr(qr, "qr_size", 300) or 300),
            logo_path=str(getattr(qr, "logo_path", None)) if getattr(qr, "logo_path", None) is not None else None,
        )
        log_message(f"✅ Erfolgreich erstellt: {filename}", level="OK")
        return "regen", filename
    except Exception as e:
        log_message(f"❌ Fehler bei {filename}: {e}", level="ERROR")
        return "error", filename


# ─────────────────────────────────────────────
# 🔄 Hauptfunktion (mit ThreadPool)
# ─────────────────────────────────────────────
def regenerate_missing_qr_codes(max_workers: int = 4) -> None:
    """Überprüft die Datenbank und regeneriert alle fehlenden QR-Code-Bilder."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = SessionLocal()
    start_time = time.time()

    try:
        qrs = session.query(QRCode).filter(QRCode.slug.isnot(None)).all()
        total = len(qrs)
        log_message(f"🔍 {total} QR-Code-Einträge gefunden – Überprüfung gestartet...")

        regenerated_count = skipped_count = error_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(regenerate_single_qr, qr) for qr in qrs]
            for future in as_completed(futures):
                status, _ = future.result()
                if status == "regen":
                    regenerated_count += 1
                elif status == "skip":
                    skipped_count += 1
                else:
                    error_count += 1

        elapsed = time.time() - start_time
        log_message("────────────────────────────────────────────")
        log_message("✅ Fertig! Zusammenfassung:")
        log_message(f"• Gesamt: {total}")
        log_message(f"• Neu generiert: {regenerated_count}")
        log_message(f"• Übersprungen: {skipped_count}")
        log_message(f"• Fehler: {error_count}")
        log_message(f"• Laufzeit: {elapsed:.2f} Sekunden")
        log_message("────────────────────────────────────────────")

    finally:
        session.close()
        log_message("💾 Datenbankverbindung geschlossen.", level="INFO")

# ─────────────────────────────────────────────
# 🚀 Main-Ausführung
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("============================================")
    print("🧠  Ouhud QR – Fehlende QR-Bilder regenerieren")
    print("============================================\n")

    log_message("📁 Starte Regenerationsprozess...", level="INFO")
    regenerate_missing_qr_codes(max_workers=6)  # 6 Threads für mehr Speed
    log_message("✅ Skript erfolgreich abgeschlossen.", level="OK")
    print(f"\n📄 Log gespeichert unter: {LOG_FILE}\n")
