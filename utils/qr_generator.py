# =============================================================================
# 🧠 QR-Code Generator – Ouhud QR
# -----------------------------------------------------------------------------
# Erstellt dynamisch gestaltete QR-Codes mit Logo, Farbverlauf, Rahmen & Text.
# =============================================================================

from __future__ import annotations
from typing import Optional, Tuple, Dict, Union
from io import BytesIO
from pathlib import Path
import os, time, logging
import qrcode
import qrcode.image.styledpil
import qrcode.image.styles.moduledrawers as mod
import qrcode.image.styles.colormasks as mask
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor

# ---------------------------------------------------------------------------
# ⚙️ Logging konfigurieren
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# 🧩 Hauptfunktion: generate_qr_png
# ---------------------------------------------------------------------------

def generate_qr_png(
    payload: str,
    size: int = 600,
    fg: str = "#0D2A78",
    bg: str = "#FFFFFF",
    logo_path: Optional[str] = None,
    module_style: str = "square",
    eye_style: str = "square",
    frame_text: Optional[str] = None,
    frame_color: str = "#4F46E5",
    gradient: Optional[Tuple[str, str]] = None,
    logo_position: str = "center",  # "center" oder "background"
    filename: Optional[str] = None,
) -> Dict[str, Union[str, bytes]]:
    """
    Generiert einen QR-Code als PNG mit Designoptionen.
    Gibt {'path': str, 'bytes': bytes} zurück.
    """

    # === 1️⃣ QR-Code Basis ===
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    # === 2️⃣ Modul-Stil ===
    module_drawer = {
        "square": mod.SquareModuleDrawer(),
        "rounded": mod.RoundedModuleDrawer(),
        "dots": mod.CircleModuleDrawer(),
        "soft": mod.GappedSquareModuleDrawer(),
    }.get(module_style, mod.SquareModuleDrawer())

    # === 3️⃣ Farbmaske (Gradient oder statisch) ===
    if gradient and len(gradient) == 2:
        start_rgb = ImageColor.getrgb(gradient[0])
        end_rgb = ImageColor.getrgb(gradient[1])
        color_mask = mask.RadialGradiantColorMask(
            center_color=start_rgb,
            edge_color=end_rgb,
        )
    else:
        color_mask = mask.SolidFillColorMask(
            front_color=ImageColor.getrgb(fg),
            back_color=ImageColor.getrgb(bg),
        )

    # === 4️⃣ QR-Code-Bild erzeugen ===
    img = qr.make_image(
        image_factory=qrcode.image.styledpil.StyledPilImage,
        module_drawer=module_drawer,
        color_mask=color_mask,
    ).convert("RGBA")

    # === 5️⃣ Logo einfügen ===
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")

            if logo_position == "background":
                bg_logo = logo.resize(img.size, Image.Resampling.LANCZOS)
                bg_logo.putalpha(180)
                img = Image.alpha_composite(bg_logo, img)

            elif logo_position == "center":
                logo_size = int(size * 0.2)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                pos = ((img.width - logo_size) // 2, (img.height - logo_size) // 2)
                img.alpha_composite(logo, dest=pos)
        except Exception as e:
            logger.warning(f"⚠️ Logo konnte nicht eingebettet werden: {e}")

    # === 6️⃣ Rahmen / Text unten ===
    if frame_text:
        padding = 80
        framed_height = img.height + padding
        framed_img = Image.new("RGBA", (img.width, framed_height), bg)
        framed_img.paste(img, (0, 0))

        draw = ImageDraw.Draw(framed_img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font = ImageFont.load_default()

        text_w = draw.textlength(frame_text, font=font)
        draw.text(
            ((img.width - text_w) // 2, img.height + 10),
            frame_text,
            fill=frame_color,
            font=font,
        )
        img = framed_img

    # === 7️⃣ Finale Skalierung & Rahmen ===
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    img = ImageOps.expand(img, border=8, fill=bg)

    # === 8️⃣ Datei speichern ===
    output_dir = Path("static/generated_qr")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = filename or f"qr_{int(time.time())}.png"
    file_path = output_dir / filename

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # ⚙️ Sicherheits-Fallback: Wenn keine Bytes vorhanden → erneut schreiben
    if buffer.getbuffer().nbytes == 0:
        logger.warning(f"⚠️ Byte-Puffer leer – regeneriere QR-Bytes ({file_path.name})")
        img.save(buffer, format="PNG")
        buffer.seek(0)

    # 💾 Datei speichern
    img.save(file_path, format="PNG")

    logger.info(f"✅ QR-Code gespeichert unter: {file_path}")
    return {"path": str(file_path), "bytes": buffer.getvalue()}
