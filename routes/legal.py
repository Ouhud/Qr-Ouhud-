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

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

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


# ---------------------------------------------------------------------
# 📩 Kontaktformular (POST)
# ---------------------------------------------------------------------
@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(
    request: Request,
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
        # 💬 Log in Konsole (Testausgabe)
        print("──────────────────────────────────────────")
        print(f"📨 Neue Kontaktanfrage:")
        print(f"👤 Name: {name}")
        print(f"📧 E-Mail: {email}")
        print(f"📝 Betreff: {subject}")
        print(f"💬 Nachricht:\n{message}")
        print("──────────────────────────────────────────")

        # ✅ Erfolgsmeldung anzeigen
        return templates.TemplateResponse(
            "kontakt.html",
            {
                "request": request,
                "success": True,
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
