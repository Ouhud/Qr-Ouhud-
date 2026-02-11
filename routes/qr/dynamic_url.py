from __future__ import annotations

import os

from fastapi import Request


def build_dynamic_url(request: Request, slug: str) -> str:
    """
    Baut eine dynamische URL passend zur aktuellen Umgebung:
    - lokal: aktueller Host (localhost/127.0.0.1)
    - prod/staging: APP_DOMAIN aus .env, sonst aktueller Host
    """
    base_url = str(request.base_url).rstrip("/")
    if "127.0.0.1" in base_url or "localhost" in base_url:
        return f"{base_url}/d/{slug}"
    app_domain = os.getenv("APP_DOMAIN", "").rstrip("/")
    return f"{(app_domain or base_url)}/d/{slug}"
