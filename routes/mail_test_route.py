# =============================================================================
# ✉️ routes/test_mail.py
# -----------------------------------------------------------------------------
# Test-Endpunkt zum Versenden einer Beispiel-Mail über utils.email_service
# -----------------------------------------------------------------------------
# Autor: Mohamad Hamza Mehmalat
# Projekt: Ouhud QR
# =============================================================================

from fastapi import APIRouter
from typing import Any
from utils.email_service import send_reset_mail

router = APIRouter(prefix="/testmail", tags=["Mail Test"])


@router.get("/", response_model=dict[str, Any])
async def testmail() -> dict[str, Any]:
    """
    Sendet eine Test-E-Mail über das konfiguriertes SMTP-Konto.
    Gibt JSON mit Status zurück.
    """
    recipient = "info@mehmalat.ch"

    try:
        send_reset_mail(
            name="Hamza",
            email=recipient,
            reset_link="https://ouhud.com/reset-test"
        )
        return {
            "recipient": recipient,
            "success": True,
            "message": "✅ Testmail erfolgreich gesendet (siehe Terminal-Log)"
        }
    except Exception as e:
        return {
            "recipient": recipient,
            "success": False,
            "message": f"❌ Fehler beim Mailversand: {str(e)}"
        }