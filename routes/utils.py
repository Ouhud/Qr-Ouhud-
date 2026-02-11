from __future__ import annotations
import os
import re
import io
from typing import Optional, Tuple
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask, RadialGradiantColorMask
from PIL import Image
from fastapi import Request, UploadFile

# 📁 Speicherort für generierte QR-Codes
UPLOAD_DIR: str = "static/generated_qr"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------------------------------------------- #
# 🌐 Hilfsfunktionen für URLs
# --------------------------------------------------------------------------- #

def normalize_url(url: str) -> str:
    """Sorgt dafür, dass eine URL mit https:// beginnt."""
    if not url:
        return ""
    url = url.strip()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    return url


def absolute_url(request: Request, path: str) -> str:
    """Erstellt eine absolute URL basierend auf der aktuellen Domain."""
    base: str = str(request.base_url).rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


# --------------------------------------------------------------------------- #
# 📤 Datei-Upload und Speicherung
# --------------------------------------------------------------------------- #

def save_upload(file: UploadFile, prefix: str, extension: str = ".png") -> str:
    """
    Speichert ein hochgeladenes File lokal ab und gibt den Pfad zurück.
    """
    filename: str = f"{prefix}_{os.urandom(4).hex()}{extension}"
    save_path: str = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(file.file.read())
    return save_path


# --------------------------------------------------------------------------- #
# 🧾 QR-Code-Erzeugung
# --------------------------------------------------------------------------- #
def _hex_to_rgb(value: str) -> Tuple[int, int, int, int]:
    """Konvertiert Hex-Farbe (#RRGGBB oder #RRGGBBAA) in RGBA."""
    value = value.lstrip("#")
    lv = len(value)
    if lv == 6:
        r, g, b = (int(value[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, 255)  # volle Deckkraft
    elif lv == 8:
        r, g, b, a = (int(value[i:i+2], 16) for i in (0, 2, 4, 6))
        return (r, g, b, a)
    else:
        # Fallback (z. B. bei fehlerhaften Eingaben)
        return (0, 0, 0, 255)

def generate_qr_png(
    payload: str,
    size: int = 600,
    fg: str = "#000000",
    bg: str = "#FFFFFF",
    logo_path: Optional[str] = None,
    module_style: str = "square",
    eye_style: str = "square",
    frame_text: Optional[str] = None,
    frame_color: str = "#4f46e5",
    gradient: Optional[Tuple[str, str]] = None,
    logo_position: str = "center",
) -> bytes:
    """
    Erzeugt einen QR-Code (PNG) mit optionalem Logo, Farbe und Text.
    Gibt die Bilddaten als Bytes zurück.
    """

    # 🧩 QR-Code konfigurieren
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H)
    qr.add_data(payload)
    qr.make(fit=True)

    # 🔳 Stil der QR-Module
    module_drawer = RoundedModuleDrawer() if module_style == "rounded" else SquareModuleDrawer()

    # 🎨 Farben oder Verlauf
    if gradient and all(gradient):
        color_mask = RadialGradiantColorMask(
            center_color=_hex_to_rgb(gradient[0]),
            edge_color=_hex_to_rgb(gradient[1]),
        )
    else:
        color_mask = SolidFillColorMask(
            back_color=_hex_to_rgb(bg),
            front_color=_hex_to_rgb(fg),
        )

    # 🖼️ QR-Code als PIL-Image erzeugen
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer,
        color_mask=color_mask
    ).convert("RGBA")

    # 🔹 Logo hinzufügen (optional)
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = size // 5
        logo.thumbnail((logo_size, logo_size))
        logo_pos = ((img.size[0] - logo.width) // 2, (img.size[1] - logo.height) // 2)
        img.paste(logo, logo_pos, mask=logo)

    # 📦 Ausgabe in Bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()