# =============================================================================
# 📘 routes/legal.py
# -----------------------------------------------------------------------------
# Enthält alle rechtlich verpflichtenden Seiten:
#   • Impressum
#   • Datenschutz
#   • Kontakt (mit Formular-POST)
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud GmbH – Ouhud QR
# =============================================================================

from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from utils.email_service import send_contact_mail

# 🔹 Templates-Verzeichnis definieren
templates = Jinja2Templates(directory="templates")

# 🔹 Router erstellen
router = APIRouter(prefix="", tags=["Legal Pages"])

PRIVACY_LAST_UPDATED = "11. Februar 2026"

# ---------------------------------------------------------------------
# 📄 Impressum
# ---------------------------------------------------------------------
@router.get("/impressum", response_class=HTMLResponse)
def impressum(request: Request):
    """Zeigt das Impressum der Ouhud GmbH."""
    return templates.TemplateResponse(
        "impressum.html",
        {"request": request, "current_year": datetime.now().year}
    )


@router.get("/impressum/", response_class=HTMLResponse)
def impressum_slash(request: Request):
    return impressum(request)


# ---------------------------------------------------------------------
# 🔒 Datenschutz
# ---------------------------------------------------------------------
@router.get("/datenschutz", response_class=HTMLResponse)
def datenschutz(request: Request):
    """Zeigt die Datenschutzrichtlinie."""
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "privacy_last_updated": PRIVACY_LAST_UPDATED,
        }
    )


@router.get("/datenschutz/", response_class=HTMLResponse)
def datenschutz_slash(request: Request):
    return datenschutz(request)


@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy_alias(request: Request):
    return datenschutz(request)


@router.get("/faq")
def faq_redirect():
    return RedirectResponse("/#faq", status_code=303)


@router.get("/faq/")
def faq_redirect_slash():
    return RedirectResponse("/#faq", status_code=303)


# ---------------------------------------------------------------------
# 📬 Kontaktformular (GET)
# ---------------------------------------------------------------------
@router.get("/kontakt", response_class=HTMLResponse)
def kontakt(request: Request):
    """Zeigt das Kontaktformular."""
    return templates.TemplateResponse(
        "kontakt.html",
        {"request": request, "current_year": datetime.now().year}
    )


@router.get("/contact", response_class=HTMLResponse)
def contact_alias(request: Request, topic: str = ""):
    """Englischer Alias für die Kontaktseite inkl. Topic-Vorbelegung."""
    normalized_topic = (topic or "").strip().lower()
    prefill_subject = ""
    prefill_message = ""

    if normalized_topic == "enterprise":
        prefill_subject = "Enterprise-Anfrage"
        prefill_message = (
            "Guten Tag Ouhud Team,\n\n"
            "wir interessieren uns für den Enterprise-Tarif.\n"
            "Bitte senden Sie uns ein individuelles Angebot inkl. API-Zugang und Onboarding.\n\n"
            "Unternehmen:\n"
            "Ansprechpartner:\n"
            "Gewünschter Start:\n\n"
            "Vielen Dank."
        )
    elif normalized_topic == "api-access":
        prefill_subject = "Anfrage API-Zugang"
        prefill_message = (
            "Guten Tag Ouhud Team,\n\n"
            "wir möchten den API-Zugang für unser Projekt anfragen.\n\n"
            "Use-Case:\n"
            "Gewünschte Integrationen:\n"
            "Geschätztes Volumen:\n\n"
            "Vielen Dank."
        )

    return templates.TemplateResponse(
        "kontakt.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "prefill_subject": prefill_subject,
            "prefill_message": prefill_message,
            "contact_topic": normalized_topic,
        },
    )


# ---------------------------------------------------------------------
# 📩 Kontaktformular (POST)
# ---------------------------------------------------------------------
@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...)
):
    """
    Verarbeitet das Kontaktformular.
    Aktuell nur als Demo: gibt Daten in der Konsole aus.
    Später kann hier eine E-Mail-Funktion (SMTP) integriert werden.
    """
    try:
        # 💬 Log in Konsole
        print("──────────────────────────────────────────")
        print(f"📨 Neue Kontaktanfrage:")
        print(f"👤 Name: {name}")
        print(f"📧 E-Mail: {email}")
        print(f"📝 Betreff: {subject}")
        print(f"💬 Nachricht:\n{message}")
        print("──────────────────────────────────────────")

        # 📬 Professioneller E-Mail-Versand (Admin + Auto-Reply)
        background_tasks.add_task(send_contact_mail, name, email, subject, message)

        # ✅ Erfolgsmeldung anzeigen
        return templates.TemplateResponse(
            "kontakt.html",
            {
                "request": request,
                "success": True,
                "prefill_subject": "",
                "prefill_message": "",
                "current_year": datetime.now().year
            }
        )
    except Exception as e:
        # ⚠️ Fehlerbehandlung
        return templates.TemplateResponse(
            "kontakt.html",
            {
                "request": request,
                "error": f"Fehler beim Senden der Nachricht: {str(e)}",
                "current_year": datetime.now().year
            }
        )
