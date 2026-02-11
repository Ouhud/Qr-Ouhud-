"""
📧 Ouhud GmbH – E-Mail-Service (professionell)
----------------------------------------------
✅ Sichere Verbindung (STARTTLS / Port 587)
✅ Zweisprachige (DE/EN) Vorlagen
✅ Automatische Antworten & Benachrichtigungen
✅ Unterstützt Kontakt, Support, Passwort-Reset
✅ Kompatibel mit FastAPI BackgroundTasks
"""

import os
import smtplib
import ssl
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from dotenv import load_dotenv
from pathlib import Path
import time




# 🔍 SMTP Debug aktivieren (zeigt alle Befehle im Terminal)
smtplib.SMTP.debuglevel = 1


# ... deine Funktionen send_contact_mail(), send_reset_mail(), ...
# ===============================================================
# 🌍 .env automatisch laden
# ===============================================================
base_dir = Path(__file__).resolve().parent
while not (base_dir / ".env").exists() and base_dir != base_dir.parent:
    base_dir = base_dir.parent
load_dotenv(base_dir / ".env")

# ===============================================================
# ⚙️ SMTP-Konfiguration
# ===============================================================
SMTP_HOST = os.getenv("SMTP_HOST", "mail.infomaniak.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

CONTACT_USER = os.getenv("SMTP_CONTACT_USER", "contact@ouhud.com")
CONTACT_PASS = os.getenv("SMTP_CONTACT_PASS", "")
CONTACT_TO = os.getenv("CONTACT_MAIL_TO", "contact@ouhud.com")

SUPPORT_USER = os.getenv("SMTP_SUPPORT_USER", "support@ouhud.com")
SUPPORT_PASS = os.getenv("SMTP_SUPPORT_PASS", "")
SUPPORT_TO = os.getenv("SUPPORT_MAIL_TO", "support@ouhud.com")

APP_DOMAIN = os.getenv("APP_DOMAIN", "https://ouhud.com")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Ouhud GmbH")
CURRENT_YEAR = datetime.now(timezone.utc).year

# ===============================================================
# 🪵 Logging konfigurieren
# ===============================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# ===============================================================
# 📬 Sichere Mail-Funktion (dynamisch mit Host-Erkennung)
# ===============================================================
def _send_mail(msg: EmailMessage, user: str, password: str):
    """
    Sicherer Versand über STARTTLS (Port 587, Infomaniak-kompatibel)
    Erkennt automatisch, ob Kontakt- oder Support-Mail benutzt wird.
    """
    import smtplib, ssl, logging, os, time

    # 🧩 Dynamische Host- und Portwahl
    if "contact@" in user.lower():
        host = os.getenv("SMTP_CONTACT_HOST", SMTP_HOST)
        port = int(os.getenv("SMTP_CONTACT_PORT", SMTP_PORT))
        logging.info("📨 Kontakt-E-Mail-Versand erkannt (contact@ouhud.com)")
    elif "support@" in user.lower():
        host = os.getenv("SMTP_SUPPORT_HOST", SMTP_HOST)
        port = int(os.getenv("SMTP_SUPPORT_PORT", SMTP_PORT))
        logging.info("🧰 Support-/System-E-Mail-Versand erkannt (support@ouhud.com)")
    else:
        host = SMTP_HOST
        port = SMTP_PORT
        logging.info("🌍 Standard-Mailversand (Fallback)")

    # 🔒 TLS-Kontext vorbereiten (Entspannt für STARTTLS auf Port 587)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.load_default_certs()

    # 🧠 Debug-Ausgabe
    logging.info("────────────────────────────────────────────")
    logging.info(f"📤 Sende E-Mail von: {user}")
    logging.info(f"📬 Empfänger: {msg['To']}")
    logging.info(f"🌐 Host: {host}:{port}")
    logging.info("────────────────────────────────────────────")

    # 🧪 Test: Prüfen, ob Thread/Lifecycle stabil läuft
    logging.info("⏱️ Starte SMTP-Verbindung (warte 3 Sekunden, um Eventloop zu testen)")
    time.sleep(3)
    logging.info("✅ Fortsetzung nach 3 Sekunden, Thread lebt noch.")

    try:
        # 📡 Verbindung aufbauen
        with smtplib.SMTP(host, port, timeout=60) as server:
            server.ehlo_or_helo_if_needed()
            code, resp = server.starttls(context=context)
            logging.info(f"🔒 STARTTLS aktiviert ({code}): {resp.decode() if isinstance(resp, bytes) else resp}")

            server.ehlo_or_helo_if_needed()
            server.login(user, password)

            # 📩 Mail versenden
            response = server.send_message(msg)
            if not response:
                logging.info(f"✅ Mail erfolgreich gesendet an: {msg['To']}")
            else:
                logging.warning(f"⚠️ Teilweise Versandfehler: {response}")

            # 🔚 Verbindung beenden (Timeout absichern)
            try:
                server.quit()
            except Exception as e:
                logging.warning(f"⚠️ QUIT unterbrochen (Mail trotzdem gesendet): {e}")

    except smtplib.SMTPAuthenticationError as e:
        err = e.smtp_error.decode() if hasattr(e, "smtp_error") else str(e)
        logging.error(f"❌ SMTP Login fehlgeschlagen: {err}")
    except smtplib.SMTPConnectError as e:
        logging.error(f"❌ Verbindung fehlgeschlagen: {e}")
    except Exception as e:
        logging.error(f"❌ Fehler beim Versand ({user} → {msg['To']}): {e}")
# ===============================================================
# 💬 Kontaktformular (zweisprachig + Auto-Reply)
# ===============================================================
def send_contact_mail(name: str, email: str, subject: str, message: str):
    """Sendet Kontaktformular-Mail an Admin und automatische Bestätigung an Benutzer."""

    # 🧩 DEBUG: Prüfen, ob Funktion aufgerufen wird
    print(f"📨 [DEBUG] send_contact_mail() wurde aufgerufen für {email} / Betreff: {subject}")
    
    # ===========================================================
    # 📩 1. Nachricht an Admin (interne Benachrichtigung)
    # ===========================================================
    admin = EmailMessage()
    admin["Subject"] = f"💬 Neue Kontaktanfrage – New Contact Request | {subject or '(kein Betreff)'}"
    admin["From"] = f"Ouhud Kontakt <{CONTACT_USER}>"
    admin["To"] = CONTACT_TO
    admin["Reply-To"] = email

    admin.add_alternative(f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;background:#f5f6fa;padding:30px;">
        <div style="max-width:640px;margin:auto;background:white;border-radius:12px;padding:30px;
                    box-shadow:0 4px 16px rgba(0,0,0,0.05);line-height:1.6;">
          
          <h2 style="color:#0D2A78;text-align:center;">💬 Neue Kontaktanfrage / New Contact Request</h2>

          <p style="font-size:15px;color:#333;">
            <strong>Von / From:</strong> {name} &lt;{email}&gt;<br>
            <strong>Betreff / Subject:</strong> {subject}
          </p>

          <div style="background:#eef2ff;border-left:4px solid #0D2A78;
                      padding:15px;margin:25px 0;border-radius:6px;">
            <p style="font-size:15px;color:#222;">{message}</p>
          </div>

          <p style="font-size:14px;color:#555;">
            Diese Nachricht wurde über das Kontaktformular von <strong>Ouhud QR</strong> gesendet.<br>
            This message was sent via the contact form on <strong>Ouhud QR</strong>.
          </p>

          <hr style="margin:30px 0;border:none;border-top:1px solid #eee;">
          <p style="font-size:12px;color:#888;text-align:center;">
            © {CURRENT_YEAR} Ouhud GmbH – All rights reserved.<br>
            <a href="https://ouhud.com" style="color:#0D2A78;text-decoration:none;">ouhud.com</a>
          </p>
        </div>
      </body>
    </html>
    """, subtype="html")

    # ===========================================================
    # 🤝 2. Automatische Antwort an Benutzer
    # ===========================================================
    reply = EmailMessage()
    reply["Subject"] = "🤝 Vielen Dank für Ihre Nachricht – Thank you for your message | Ouhud GmbH"
    reply["From"] = f"Ouhud Kontakt <{CONTACT_USER}>"
    reply["To"] = email

    reply.add_alternative(f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;background:#f5f6fa;padding:30px;">
        <div style="max-width:640px;margin:auto;background:white;border-radius:12px;padding:30px;
                    box-shadow:0 4px 16px rgba(0,0,0,0.05);line-height:1.6;">
          
          <h2 style="color:#0D2A78;text-align:center;">🤝 Vielen Dank für Ihre Nachricht!</h2>
          <p style="font-size:15px;color:#333;">
            Sehr geehrte/r {name},<br><br>
            wir haben Ihre Anfrage erhalten und melden uns innerhalb von <b>24–48 Stunden</b> bei Ihnen.<br>
            Bei dringenden Anliegen können Sie uns jederzeit über <a href="mailto:support@ouhud.com" style="color:#0D2A78;">support@ouhud.com</a> erreichen.
          </p>

          <hr style="margin:25px 0;border:none;border-top:1px solid #eee;">

          <h3 style="color:#0D2A78;">🇬🇧 Thank you for your message!</h3>
          <p style="font-size:15px;color:#333;">
            Dear {name},<br><br>
            We have received your inquiry and will get back to you within <b>24–48 hours</b>.<br>
            For urgent matters, feel free to contact us at 
            <a href="mailto:support@ouhud.com" style="color:#0D2A78;">support@ouhud.com</a>.
          </p>

          <hr style="margin:30px 0;border:none;border-top:1px solid #eee;">
          <p style="font-size:12px;color:#888;text-align:center;">
            © {CURRENT_YEAR} Ouhud GmbH – All rights reserved.<br>
            <a href="https://ouhud.com" style="color:#0D2A78;text-decoration:none;">ouhud.com</a>
          </p>
        </div>
      </body>
    </html>
    """, subtype="html")

    # ===========================================================
    # 📤 Versand beider E-Mails
    # ===========================================================
    # 📤 1. Mail an Admin (interne Benachrichtigung)
    try:
        _send_mail(admin, CONTACT_USER, CONTACT_PASS)
        logging.info("✅ Admin-Mail erfolgreich gesendet.")
    except Exception as e:
        logging.error(f"❌ Fehler beim Senden der Admin-Mail: {e}")

    # 📤 2. Mail an Benutzer (Auto-Reply)
    try:
        import time
        time.sleep(1)  # kleine Pause, um SMTP sauber zu trennen
        _send_mail(reply, CONTACT_USER, CONTACT_PASS)
        logging.info(f"✅ Auto-Reply erfolgreich gesendet an {email}.")
    except Exception as e:
        logging.error(f"❌ Fehler beim Senden der Auto-Reply-Mail: {e}")

# ===============================================================
# 🧰 Support-Mail
# ===============================================================
def send_support_mail(name: str, email: str, subject: str, message: str):
    msg = EmailMessage()
    msg["Subject"] = f"🧰 Supportanfrage – {subject or '(kein Betreff)'}"
    msg["From"] = f"Ouhud Support <{SUPPORT_USER}>"
    msg["To"] = SUPPORT_TO
    msg["Reply-To"] = email
    msg.add_alternative(f"""
    <html><body style="font-family:Arial;background:#f9fafb;padding:25px;">
      <div style="max-width:600px;margin:auto;background:white;padding:25px;border-radius:10px;">
        <h2 style="color:#0D2A78;">🧰 Neue Supportanfrage</h2>
        <p><b>Von:</b> {name} &lt;{email}&gt;</p>
        <p><b>Betreff:</b> {subject}</p>
        <div style="background:#eef2ff;border-left:4px solid #0D2A78;padding:12px;margin:18px 0;">
          {message}
        </div>
        <p style="font-size:12px;color:#666;text-align:center;">Gesendet über <a href="{APP_DOMAIN}">{APP_DOMAIN}</a></p>
      </div>
    </body></html>
    """, subtype="html")

    _send_mail(msg, SUPPORT_USER, SUPPORT_PASS)

# ===============================================================
# 🔒 Passwort-Reset (zweisprachig, professionell)
# ===============================================================
def send_reset_mail(name: str, email: str, reset_link: str):
    msg = EmailMessage()
    msg["Subject"] = "🔐 Passwort zurücksetzen – Reset your password | Ouhud QR"
    msg["From"] = f"Ouhud Support <{SUPPORT_USER}>"
    msg["To"] = email

    msg.add_alternative(f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;background:#f5f6fa;padding:30px;">
        <div style="max-width:640px;margin:auto;background:white;border-radius:12px;padding:30px;
                    box-shadow:0 4px 16px rgba(0,0,0,0.05);line-height:1.6;">

          <h2 style="color:#0D2A78;text-align:center;">🔒 Passwort zurücksetzen / Reset your password</h2>

          <p style="font-size:15px;color:#333;">
            Hallo {name},<br><br>
            Sie haben eine Anfrage gestellt, um Ihr Passwort für <strong>Ouhud QR</strong> zurückzusetzen.<br>
            Klicken Sie auf den Button unten, um ein neues Passwort zu erstellen:
          </p>

          <div style="text-align:center;margin:25px;">
            <a href="{reset_link}" 
               style="background:#0D2A78;color:#fff;padding:14px 28px;
                      border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
               🔑 Passwort jetzt zurücksetzen
            </a>
          </div>

          <p style="font-size:14px;color:#555;">
            Falls Sie <strong>keine</strong> Passwortänderung angefordert haben,
            ignorieren Sie bitte diese E-Mail – Ihr Konto bleibt sicher.<br>
            Der Link ist aus Sicherheitsgründen nur für begrenzte Zeit gültig.
          </p>

          <hr style="margin:30px 0;border:none;border-top:1px solid #eee;">

          <p style="font-size:15px;color:#333;">
            Dear {name},<br><br>
            You recently requested to reset your password for <strong>Ouhud QR</strong>.<br>
            Click the button below to choose a new one:
          </p>

          <div style="text-align:center;margin:25px;">
            <a href="{reset_link}" 
               style="background:#0D2A78;color:#fff;padding:14px 28px;
                      border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
               🔑 Reset Password Now
            </a>
          </div>

          <p style="font-size:14px;color:#555;">
            If you did <strong>not</strong> request this password reset,
            please ignore this email – your account remains safe.<br>
            For security reasons, this link will expire automatically.
          </p>

          <hr style="margin:30px 0;border:none;border-top:1px solid #eee;">
          <p style="font-size:12px;color:#888;text-align:center;">
            © {CURRENT_YEAR} Ouhud GmbH – All rights reserved.<br>
            <a href="https://ouhud.com" style="color:#0D2A78;text-decoration:none;">ouhud.com</a>
          </p>
        </div>
      </body>
    </html>
    """, subtype="html")

    _send_mail(msg, SUPPORT_USER, SUPPORT_PASS)

# ===============================================================
# 🧪 Test (lokal)
# ===============================================================
if __name__ == "__main__":
    print("== TEST 1: Passwort-Reset ==")
    send_reset_mail("Hamza", "info@mehmalat.ch", f"{APP_DOMAIN}/reset/test")

    print("\n== TEST 2: Kontaktformular ==")
    send_contact_mail("Hamza Mehmalat", "info@mehmalat.ch", "Testformular", "Dies ist eine Testnachricht von Ouhud QR.")

    print("\n== TEST 3: Support ==")
    send_support_mail("Hamza Mehmalat", "info@mehmalat.ch", "Test Support", "Ich teste den Support-Mailversand.")
