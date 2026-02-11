from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
from io import BytesIO
from typing import Optional
from urllib.parse import quote

import qrcode
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def generate_base32_secret(length: int = 32) -> str:
    """Erzeugt einen Base32-Secret-Key für TOTP."""
    raw = os.urandom(length)
    return base64.b32encode(raw).decode("ascii").replace("=", "")


def _normalize_secret(secret: str) -> bytes:
    normalized = (secret or "").strip().replace(" ", "").upper()
    pad_len = (-len(normalized)) % 8
    normalized += "=" * pad_len
    return base64.b32decode(normalized, casefold=True)


def totp_code(secret: str, for_time: Optional[int] = None, step: int = 30, digits: int = 6) -> str:
    """Berechnet TOTP-Code gemäß RFC 6238 (HMAC-SHA1)."""
    ts = int(for_time or time.time())
    counter = int(ts // step)
    key = _normalize_secret(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    code = binary % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """Prüft TOTP-Code mit kleinem Zeitfenster (default ±30s)."""
    clean = (code or "").strip().replace(" ", "")
    if not clean.isdigit() or len(clean) != 6:
        return False

    now = int(time.time())
    for offset in range(-window, window + 1):
        if totp_code(secret, for_time=now + (offset * 30)) == clean:
            return True
    return False


def build_otpauth_uri(secret: str, account_name: str, issuer: str = "Ouhud QR") -> str:
    label = quote(f"{issuer}:{account_name}")
    issuer_q = quote(issuer)
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer_q}&algorithm=SHA1&digits=6&period=30"


def qr_data_uri(payload: str) -> str:
    """Generiert Data-URI PNG für QR-Anzeige im HTML."""
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def ensure_2fa_columns(engine: Engine) -> None:
    """
    Sichert, dass 2FA-Spalten auf users existieren.
    Läuft idempotent beim App-Start.
    """
    try:
        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("users")}
        dialect = engine.dialect.name.lower()

        statements: list[str] = []
        if "two_factor_enabled" not in cols:
            if dialect == "sqlite":
                statements.append("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0")
            else:
                statements.append("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0")
        if "two_factor_secret" not in cols:
            if dialect == "sqlite":
                statements.append("ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(128)")
            else:
                statements.append("ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(128) NULL")

        if not statements:
            return

        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
        print("✅ 2FA-Spalten geprüft/ergänzt.")
    except Exception as exc:
        print(f"⚠️ Konnte 2FA-Spalten nicht automatisch ergänzen: {exc}")
