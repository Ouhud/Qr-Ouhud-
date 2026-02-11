from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

LOGO_DIR = Path("static/logos")
LOGO_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def save_qr_logo(upload: UploadFile | None, slug: str, prefix: str = "qr_logo") -> Tuple[Optional[str], Optional[str]]:
    """Save uploaded logo and return (filesystem_path, public_path)."""
    if not upload or not upload.filename:
        return None, None

    ext = Path(upload.filename).suffix.lower() or ".png"
    if ext not in ALLOWED_EXTENSIONS:
        return None, None

    filename = f"{prefix}_{slug}{ext}"
    fs_path = LOGO_DIR / filename
    with open(fs_path, "wb") as f:
        f.write(upload.file.read())

    public_path = f"/static/logos/{filename}"
    return str(fs_path), public_path
