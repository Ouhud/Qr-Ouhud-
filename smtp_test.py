import smtplib, ssl, logging

host = "mail.infomaniak.com"
port = 587
user = "contact@ouhud.com"
password = "Gloria28082022@"
to = "info@mehmalat.ch"

logging.basicConfig(level=logging.DEBUG)

context = ssl.create_default_context()

print("🔍 Verbinde mit SMTP-Server ...")
server = smtplib.SMTP(host, port, timeout=30)
server.set_debuglevel(1)
server.ehlo()
print("✅ Verbindung hergestellt, starte STARTTLS ...")
server.starttls(context=context)
server.ehlo()
print("🔐 Login ...")
server.login(user, password)
print("✅ Login erfolgreich!")

msg = f"From: {user}\nTo: {to}\nSubject: Testmail direkt per SMTP\n\nDies ist ein direkter Test von Hamza."
print("📤 Sende Mail ...")
server.sendmail(user, [to], msg)
print("✅ Mail gesendet!")
server.quit()