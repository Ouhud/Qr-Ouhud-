# =============================================================================
# 🔐 utils/encryption.py
# Verschlüsselung für QR-Inhalte (AES-256-GCM)
# =============================================================================

from __future__ import annotations
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any, Optional
import hashlib

# =============================================================================
# 🔑 Encryption Key Management
# =============================================================================

def get_encryption_key() -> bytes:
    """
    Lädt den Encryption Key aus der Umgebungsvariable.
    Falls nicht vorhanden, wird ein neuer Key generiert.
    """
    env_key = os.getenv("ENCRYPTION_KEY")
    
    if env_key:
        # Key aus Environment (sollte 32 bytes sein für AES-256)
        key_bytes = env_key.encode() if env_key else b''
        # Auf 32 bytes kürzen oder padding
        if len(key_bytes) > 32:
            key_bytes = key_bytes[:32]
        elif len(key_bytes) < 32:
            # Pad mit Nullen wenn zu kurz
            key_bytes = key_bytes + b'\x00' * (32 - len(key_bytes))
        return key_bytes
    else:
        # Generate a new key for first run
        new_key = os.urandom(32)
        print("⚠️  ENCRYPTION_KEY not set! Generated key (add to .env):")
        print(f"ENCRYPTION_KEY={new_key.hex()}")
        return new_key


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Leitet einen Encryption Key von einem Passwort ab.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return kdf.derive(password.encode())


# =============================================================================
# 🔐 AES-256-GCM Encryption/Decryption
# =============================================================================

class QRContentEncryption:
    """
    Verschlüsselt und entschlüsselt QR-Inhalte mit AES-256-GCM.
    Jeder QR-Code erhält seinen eigenen zufälligen Salt und IV.
    """
    
    def __init__(self):
        self._key = get_encryption_key()
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Verschlüsselt ein Dictionary zu einem Base64-String.
        Format: base64(salt || iv || ciphertext || tag)
        """
        if not data:
            return ""
        
        # Salt für Key-Derivation (pro QR-Code eindeutig)
        salt = os.urandom(16)
        
        # IV für AES-GCM
        iv = os.urandom(12)
        
        # Key ableiten
        derived_key = derive_key(self._key.hex(), salt)
        
        # AES-GCM Cipher erstellen
        aesgcm = AESGCM(derived_key)
        
        # JSON serialisieren
        import json
        plaintext = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # Verschlüsseln
        ciphertext = aesgcm.encrypt(iv, plaintext, None)
        
        # Zusammenfügen: salt + iv + ciphertext
        combined = salt + iv + ciphertext
        
        return base64.b64encode(combined).decode('ascii')
    
    def decrypt(self, encrypted_data: str) -> Optional[Dict[str, Any]]:
        """
        Entschlüsselt einen Base64-String zurück zu einem Dictionary.
        """
        if not encrypted_data:
            return None
        
        try:
            # Base64 dekodieren
            combined = base64.b64decode(encrypted_data.encode('ascii'))
            
            # Extrahieren: salt (16 bytes), iv (12 bytes), rest ist ciphertext
            salt = combined[:16]
            iv = combined[16:28]
            ciphertext = combined[28:]
            
            # Key ableiten
            derived_key = derive_key(self._key.hex(), salt)
            
            # AES-GCM Cipher erstellen
            aesgcm = AESGCM(derived_key)
            
            # Entschlüsseln
            plaintext = aesgcm.decrypt(iv, ciphertext, None)
            
            # JSON deserialisieren
            import json
            return json.loads(plaintext.decode('utf-8'))
            
        except Exception as e:
            # Kein lautes Logging im Normalbetrieb: alte/inkonsistente Daten
            # können vorkommen und werden durch Fallback-Logik behandelt.
            if os.getenv("DEBUG_ENCRYPTION") == "1":
                print(f"❌ Decryption failed: {e}")
            return None


# =============================================================================
# 🔧 Simple API (Singleton Pattern)
# =============================================================================

_encryption_instance: Optional[QRContentEncryption] = None


def get_encryptor() -> QRContentEncryption:
    """Gibt die Singleton-Instanz des Encryptors zurück."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = QRContentEncryption()
    return _encryption_instance


def encrypt_qr_content(data: Dict[str, Any]) -> str:
    """Verschlüsselt QR-Inhalte."""
    return get_encryptor().encrypt(data)


def decrypt_qr_content(encrypted_data: str) -> Optional[Dict[str, Any]]:
    """Entschlüsselt QR-Inhalte."""
    return get_encryptor().decrypt(encrypted_data)
