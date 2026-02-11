"""
📩 Kontaktmodul – Ouhud GmbH (stabile & asynchrone Version)
────────────────────────────────────────────
Dieses Modul verarbeitet das Kontaktformular der Ouhud-Website.

Funktionen:
- GET  /kontakt   → Zeigt das Kontaktformular
- POST /contact   → Sendet Nachricht per E-Mail an das Ouhud-Team
                    + Auto-Reply an Absender
- GET  /testmail  → Entwicklertest zum Prüfen des Mailversands

Abhängigkeiten:
- utils.email_service → send_contact_mail()
- templates/kontakt.html → Formularseite
- templates/contact_success.html → Erfolgsseite
- templates/contact_error.html → Fehlerseite
"""

# ─────────────────────────────────────────────
# 📦 Standardimporte
# ─────────────────────────────────────────────
from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import asyncio
from utils.email_service import send_contact_mail

# ─────────────────────────────────────────────
# ⚙️ Logging-Konfiguration
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("ouhud.contact")

# ─────────────────────────────────────────────
# 🧩 Router & Templates
# ─────────────────────────────────────────────
router = APIRouter(tags=["Kontakt"])
templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────────
# 📄 Kontaktformular anzeigen
# ─────────────────────────────────────────────
@router.get("/kontakt", response_class=HTMLResponse)
def kontakt_form(request: Request):
    logger.info("🌐 Kontaktformular aufgerufen (/kontakt)")
    return templates.TemplateResponse("kontakt.html", {"request": request})

# ─────────────────────────────────────────────
# 📬 Kontaktformular absenden (hybride async-Version)
# ─────────────────────────────────────────────
@router.post("/contact", response_class=HTMLResponse)
async def kontakt_send(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...),
):
    logger.info("────────────────────────────────────────────")
    logger.info("📨 Neue Kontaktanfrage empfangen:")
    logger.info("👤 %s", name)
    logger.info("📧 %s", email)
    logger.info("📝 %s", subject or "(kein Betreff)")
    logger.info("💬 %s", message)
    logger.info("────────────────────────────────────────────")

    try:
        # 🧩 Versuch 1: BackgroundTask (FastAPI-intern)
        try:
            background_tasks.add_task(send_contact_mail, name, email, subject, message)
            logger.info("🧩 BackgroundTask für Mailversand gestartet (FastAPI).")
        except Exception as bg_err:
            logger.warning("⚠️ BackgroundTask-Fehler, weiche auf Thread aus: %s", bg_err)
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, send_contact_mail, name, email, subject, message)
            logger.info("🚀 Mailversand über Thread gestartet (run_in_executor).")

        # ✅ Erfolgsseite anzeigen
        return templates.TemplateResponse(
            "contact_success.html",
            {
                "request": request,
                "name": name,
                "email": email,
                "subject": subject,
            },
        )

    except Exception as e:
        logger.exception("❌ Fehler beim Senden der Kontaktanfrage: %s", e)
        return templates.TemplateResponse(
            "contact_error.html",
            {
                "request": request,
                "error": str(e),
                "name": name,
                "email": email,
            },
            status_code=500,
        )
