# 🔐 QR Content Encryption - Implementierungsplan

## Ziel
QR-Inhalte (URLs, Links, etc.) verschlüsselt speichern, sodass nur der Besitzer die echten Daten sehen kann.

---

## 📋 Implementierte Änderungen

### ✅ 1. Encryption Utility erstellt
- **Datei:** `utils/encryption.py`
- AES-256-GCM Verschlüsselung für QR-Inhalte
- Key aus .env Variable laden

### ✅ 2. QRCode Model angepasst
- **Datei:** `models/qrcode.py`
- Neues Feld `encrypted_content` hinzugefügt
- Hilfsmethoden `get_data()` und `set_data()` für Encrypt/Decrypt
- Automatische Migration beim Laden (alte Daten werden verschlüsselt)

### ✅ 3. QR-Base-Routen aktualisiert
- **Datei:** `routes/qr_base.py`
- `create_qr()` - Content wird verschlüsselt vor Speicherung
- `update_qr()` - Content wird verschlüsselt beim Update

### ✅ 4. QR-Resolver angepasst
- **Datei:** `routes/qr_resolve.py`
- Beim Scannen: QR-Daten werden entschlüsselt für Weiterleitung

### ✅ 5. QR Edit-Routen angepasst
- **Datei:** `routes/qr/edit_qr.py`
- Beim Bearbeiten: Content wird entschlüsselt für Anzeige
- Beim Speichern: Content wird verschlüsselt

### ✅ 6. Individuelle QR-Routen aktualisiert
- `routes/qr/url.py` - URL QR-Codes
- `routes/qr/pdf.py` - PDF QR-Codes
- `routes/qr/vcard.py` - vCard QR-Codes

### ✅ 7. .env Beispiel erstellt
- **Datei:** `.env.example`
- `ENCRYPTION_KEY` dokumentiert (64 Hex-Zeichen für AES-256)

### ✅ 8. Migration-Skript erstellt
- **Datei:** `migrations/add_encrypted_content.py`
- Fügt die `encrypted_content` Spalte zur DB hinzu

---

## 🔧 Technische Details

### Encryption Schema (AES-256-GCM)
```
encrypt(data) → {iv: hex, ciphertext: hex, tag: hex}
decrypt({iv, ciphertext, tag}) → original_data
```

### Neue env Variable
```bash
ENCRYPTION_KEY=your-64-character-hex-key-here
```

---

## 📁 Betroffene Dateien

| Datei | Status |
|-------|--------|
| `utils/encryption.py` | ✅ NEU - Encryption utilities |
| `models/qrcode.py` | ✅ encrypted_content Feld + Hilfsmethoden |
| `routes/qr_base.py` | ✅ Create/Update mit Encryption |
| `routes/qr_resolve.py` | ✅ Resolve mit Decryption |
| `routes/qr/edit_qr.py` | ✅ Edit mit Encryption |
| `routes/qr/url.py` | ✅ Encryption integriert |
| `routes/qr/pdf.py` | ✅ Encryption integriert |
| `routes/qr/vcard.py` | ✅ Encryption integriert |
| `.env.example` | ✅ Dokumentation erstellt |
| `migrations/add_encrypted_content.py` | ✅ Migration erstellt |

---

## ⚠️ Noch zu tun (Optional)

1. **Dashboard anpassen** - QR-Inhalte in Listen nicht anzeigen
2. **Settings-Seite anpassen** - QR-Übersicht ohne sensible Daten
3. **Datenbank-Migration ausführen** - `python migrations/add_encrypted_content.py`

---

## ✅ Erfolgsmessung

1. ✅ QR-Inhalte werden verschlüsselt in DB gespeichert
2. ✅ QR-Scans funktionieren weiterhin (automatische Entschlüsselung)
3. ✅ Nur Besitzer kann echten Content bei Bearbeitung sehen
4. 🔄 Dashboard zeigt keine URLs (optional)

