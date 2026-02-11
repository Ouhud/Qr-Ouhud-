from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def billing_exempt_emails() -> set[str]:
    raw = os.getenv("BILLING_EXEMPT_EMAILS", "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def billing_exempt_domains() -> set[str]:
    raw = os.getenv("BILLING_EXEMPT_DOMAINS", "")
    return {item.strip().lower().lstrip("@") for item in raw.split(",") if item.strip()}


def is_billing_exempt_email(email: str | None) -> bool:
    normalized = _normalized(email)
    if not normalized:
        return False
    if normalized in billing_exempt_emails():
        return True
    if "@" not in normalized:
        return False
    domain = normalized.rsplit("@", 1)[1]
    return domain in billing_exempt_domains()


def is_billing_exempt_user(user: Any) -> bool:
    user_email = getattr(user, "email", None)
    return is_billing_exempt_email(user_email)
