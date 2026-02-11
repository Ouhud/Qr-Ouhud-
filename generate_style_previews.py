# ===========================================================
# 🖼️ QR-Stil-Preview Generator für Ouhud QR
# ===========================================================
# Erzeugt automatisch QR-Vorschau-Bilder für alle Designs
# und speichert sie unter static/style_previews/
# ===========================================================

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import qrcode
from typing import Tuple

# 📁 Zielordner für Previews
PREVIEW_DIR = Path("static/style_previews")
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

# Beispiel-QR-Inhalt
QR_DATA = "https://ouhud.com/demo"

# 🎨 Farbdefinitionen pro Stil
STYLES = {
    "classic": {"fg": "#000000", "bg": "#FFFFFF"},
    "rounded": {"fg": "#0D2A78", "bg": "#F8FAFC"},
    "dots": {"fg": "#2563EB", "bg": "#E0E7FF"},
    "soft": {"fg": "#4F46E5", "bg": "#EEF2FF"},
    "gradient": {"fg": "#7C3AED", "bg": "#E0E7FF"},
    "premium": {"fg": "#D4AF37", "bg": "#FFFBEA"},
    "neon": {"fg": "#22D3EE", "bg": "#0F172A"},
    "dark": {"fg": "#FFFFFF", "bg": "#0D0D0D"},
    "sunset": {"fg": "#F97316", "bg": "#FFF7ED"},
    "ocean": {"fg": "#0EA5E9", "bg": "#E0F2FE"},
    "forest": {"fg": "#15803D", "bg": "#ECFDF5"},
    "rose": {"fg": "#BE185D", "bg": "#FFF1F2"},
}

# ✨ Neue 3D-Designs hinzufügen
STYLES.update({
    "3d_pro": {"fg": "#0d2a78", "bg": "#ffffff"},
    "metallic": {"fg": "#5f5f5f", "bg": "#f9f9f9"},
    "glass": {"fg": "#0d2a78", "bg": "#e6f0ff"},
    "futuristic": {"fg": "#00ffff", "bg": "#0a0a0a"},
    "holo": {"fg": "#ff99ff", "bg": "#e6e6ff"},
    "ouhud": {"fg": "#0d2a78", "bg": "#edf2ff"},
})


# 🔸 Gradient-Helfer
def make_gradient(size: Tuple[int, int] = (300, 300),
                  c1: str = "#7C3AED", c2: str = "#E0E7FF") -> Image.Image:
    """Erzeugt einfachen vertikalen Farbverlauf."""
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)
    mask = Image.linear_gradient("L").resize(size)
    return Image.composite(base, top, mask)


# 🔸 3D-Effekt
def apply_3d_effect(img: Image.Image) -> Image.Image:
    """Erzeugt Tiefenwirkung durch Schatten."""
    shadow = img.copy().convert("RGBA")
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    shadow = ImageEnhance.Brightness(shadow).enhance(0.4)
    result = Image.new("RGBA", (img.width + 20, img.height + 20), (255,255,255,0))
    result.paste(shadow, (10,10), shadow)
    result.paste(img, (0,0), img)
    return result


# 🧩 QR-Bilder pro Stil generieren
for name, conf in STYLES.items():
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(QR_DATA)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=conf["fg"], back_color=conf["bg"]).convert("RGBA")

    # 🔹 Stilabhängige Effekte
    if name == "rounded":
        mask = Image.new("L", qr_img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, qr_img.size[0], qr_img.size[1]), radius=40, fill=255)
        qr_img.putalpha(mask)

    elif name == "dots":
        qr_img = qr_img.filter(ImageFilter.CONTOUR)

    elif name == "soft":
        qr_img = qr_img.filter(ImageFilter.SMOOTH_MORE)

    elif name == "gradient":
        bg = make_gradient(qr_img.size, "#6366F1", "#E0E7FF")
        qr_img = Image.alpha_composite(bg.convert("RGBA"), qr_img)

    elif name == "premium":
        bg = Image.new("RGBA", qr_img.size, "#FFFBEA")
        gold = Image.new("RGBA", qr_img.size, "#FFD70033")
        qr_img = Image.alpha_composite(bg, qr_img)
        qr_img = Image.alpha_composite(qr_img, gold)

    elif name == "neon":
        overlay = Image.new("RGBA", qr_img.size, "#22D3EE44")
        qr_img = Image.alpha_composite(overlay, qr_img)

    elif name == "dark":
        qr_img = qr.make_image(fill_color="#FFFFFF", back_color="#0D0D0D").convert("RGBA")

    elif name == "3d_pro":
        qr_img = apply_3d_effect(qr_img)

    elif name == "metallic":
        qr_img = qr_img.filter(ImageFilter.SMOOTH)
        metallic_overlay = Image.new("RGBA", qr_img.size, (220, 220, 220, 60))
        qr_img = Image.alpha_composite(qr_img, metallic_overlay)

    elif name == "glass":
        blur = qr_img.filter(ImageFilter.GaussianBlur(3))
        overlay = Image.new("RGBA", qr_img.size, (255,255,255,100))
        qr_img = Image.alpha_composite(blur, overlay)

    elif name == "futuristic":
        glow = qr_img.filter(ImageFilter.GaussianBlur(6))
        qr_img = Image.alpha_composite(glow, qr_img)

    elif name == "holo":
        gradient = make_gradient(qr_img.size, "#00FFFF", "#FF00FF")
        qr_img = Image.alpha_composite(gradient.convert("RGBA"), qr_img)

    elif name == "ouhud":
        glow = qr_img.filter(ImageFilter.GaussianBlur(4))
        overlay = Image.new("RGBA", qr_img.size, "#0d2a7844")
        qr_img = Image.alpha_composite(overlay, qr_img)

    # 🔸 Logo in der Mitte (optional)
    logo_path = Path("static/logo/ouhud_logo.png")
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        qr_w, qr_h = qr_img.size
        logo_size = int(qr_w * 0.15)
        logo = logo.resize((logo_size, logo_size))
        pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
        qr_img.paste(logo, pos, logo)

    # 💾 Speichern
    out_path = PREVIEW_DIR / f"{name}.png"
    qr_img.save(out_path)
    print(f"✅ {name}.png erstellt -> {out_path}")

print("\n🎨 Alle QR-Vorschauen erfolgreich generiert!")