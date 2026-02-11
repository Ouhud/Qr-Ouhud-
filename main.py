# =============================================================================
# 🚀 Ouhud QR – Hauptapplikation (main.py)
# =============================================================================

from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

from dotenv import load_dotenv
from typing import List, Dict

from database import engine
from utils.two_factor import ensure_2fa_columns
from utils.login_devices import ensure_login_devices_table
from utils.engagement_tables import ensure_engagement_tables
from utils.enterprise_tables import ensure_enterprise_tables
from utils.api_keys import ensure_api_key_columns, ensure_api_keys_table

# -------------------------------------------------------------------------
# 1️⃣ .env laden (muss ganz oben sein!)
# -------------------------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
print("🧩 Lade .env von:", env_path)
load_dotenv(dotenv_path=env_path)

# -------------------------------------------------------------------------
# 2️⃣ FastAPI App
# -------------------------------------------------------------------------
app = FastAPI(title="Ouhud QR", version="2.0")
ensure_2fa_columns(engine)
ensure_login_devices_table(engine)
ensure_engagement_tables(engine)
ensure_enterprise_tables(engine)
ensure_api_key_columns(engine)
ensure_api_keys_table(engine)

# -------------------------------------------------------------------------
# 3️⃣ Templates & Static
# -------------------------------------------------------------------------
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------------------
# 4️⃣ Session Middleware
# -------------------------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "ouhud-secret-key"),
    max_age=60 * 60 * 24 * 7,
)

# -------------------------------------------------------------------------
# 5️⃣ Routen laden – NUR die neuen, modularen Router
# -------------------------------------------------------------------------
from routes import auth
from routes import dashboard
from routes import qr_base
from routes import qr_resolve   # für /d/<slug>
from routes import dyn
from routes import user_profile
from routes import settings
from routes import team
from routes import sla
from routes import api
from routes import legal

# Individual QR Routes
from routes.qr import (
    url,
    vcard,
    pdf,
    wifi,
    email,
    sms,
    tel,
    social,
    event,
    geo,
    multilink,
    product,
    payment,
    edit_qr,
    wallet,
    gs1,
    app_deeplink,
    review,
    booking,
    lead,
    feedback,
    coupon,
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(user_profile.router)
app.include_router(settings.router)
app.include_router(team.router)
app.include_router(sla.router)
app.include_router(api.router)
app.include_router(legal.router)

# zentrale QR-Erstellung
app.include_router(qr_base.router)

# zentraler Resolver
app.include_router(qr_resolve.router)
app.include_router(dyn.router)

# Individual QR Type Routes
app.include_router(url.router)
app.include_router(vcard.router)
app.include_router(pdf.router)
app.include_router(wifi.router)
app.include_router(email.router)
app.include_router(sms.router)
app.include_router(tel.router)
app.include_router(social.router)
app.include_router(event.router)
app.include_router(geo.router)
app.include_router(multilink.router)
app.include_router(product.router)
app.include_router(payment.router)
app.include_router(wallet.router)
app.include_router(gs1.router)
app.include_router(app_deeplink.router)
app.include_router(review.router)
app.include_router(booking.router)
app.include_router(lead.router)
app.include_router(feedback.router)
app.include_router(coupon.router)

# Central edit routes for all QR types
app.include_router(edit_qr.router)

# -------------------------------------------------------------------------
# 6️⃣ Home
# -------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------------------------------------------------
# 6.1️⃣ Example QR Image
# -------------------------------------------------------------------------
@app.get("/example-qr")
def example_qr():
    return FileResponse("static/default-qr.png", media_type="image/png")

# -------------------------------------------------------------------------
# 6.2️⃣ Service Worker
# -------------------------------------------------------------------------
@app.get("/sw.js")
def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript")

# -------------------------------------------------------------------------
# 7️⃣ Debug Route
# -------------------------------------------------------------------------
@app.get("/debug/routes")
def debug_routes() -> List[Dict[str, str]]:
    return [{"path": r.path, "name": r.name} for r in app.routes]
