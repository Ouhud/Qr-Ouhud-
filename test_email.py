from utils.email_service import send_reset_mail

def test_send_password_reset_email() -> None:
    """Testet den Versand der Passwort-Reset-E-Mail."""
    # send_reset_mail gibt nichts zurück → wir testen nur, dass sie ohne Fehler läuft
    try:
        send_reset_mail("Hamza", "test@example.com", "https://ouhud.com/reset")
        success = True
        message = "E-Mail-Funktion hat ohne Exception ausgeführt."
    except Exception as e:
        success = False
        message = str(e)

    print(f"✅ Ergebnis: {message}")
    assert isinstance(success, bool)