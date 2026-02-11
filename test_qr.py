from utils.qr_generator import generate_qr_png
from utils.qr_config import get_qr_style
import os

# --- Design laden ---
style = get_qr_style("modern")

# --- QR-Code generieren ---
qr_bytes = generate_qr_png(
    payload="https://ouhud.com",
    size=style["size"],
    fg=style["fg"],
    bg=style["bg"],
    gradient=style["gradient"],
    frame_color=style["frame_color"],
    logo_path="static/logos/ouhud_logo.png",
    logo_position="background",
    frame_text="Ouhud QR – Smart Links",
)

# --- Datei speichern ---
os.makedirs("static/qr_codes", exist_ok=True)
with open("static/qr_codes/test_ouhud.png", "wb") as f:
    f.write(qr_bytes["bytes"])

print("✅ QR-Code erfolgreich generiert: static/qr_codes/test_ouhud.png")