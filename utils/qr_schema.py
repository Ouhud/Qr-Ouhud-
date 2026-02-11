# utils/qr_schema.py
"""
Definiert Validierungsregeln für jeden QR-Code-Typ.
Damit ist save_qr() 100% dynamisch & sicher.
"""

from typing import Dict, Any


# ✅ MINIMALE Felder pro QR-Typ
QR_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "sms": {
        "required": ["phone"],
        "optional": ["message"]
    },
    "url": {
        "required": ["url"]
    },
    "vcard": {
        "required": ["first_name", "last_name", "email"],
        "optional": ["address", "city", "zip", "country", "website", "phone"]
    },
    "wifi": {
        "required": ["ssid", "auth"],
        "optional": ["password"]
    },
    "geo": {
        "required": ["lat", "lon"]
    },
    "event": {
        "required": ["title", "start", "end"]
    },
    "email": {
        "required": ["email"],
        "optional": ["subject", "body"]
    },
    "phone": {
        "required": ["phone"]
    },
    "product": {
        "required": ["name", "price"],
        "optional": ["currency", "description"]
    },
    "social": {
        "required": [],
        "optional": ["facebook", "instagram", "linkedin", "youtube", "website"]
    }
}