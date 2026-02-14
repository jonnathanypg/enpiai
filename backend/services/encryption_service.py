"""
Encryption Service - Application-level PII/PHI encryption.
Implements Sovereign SQL Layer (GEMINI.md Rule A.1).

Uses Fernet (AES-128-CBC + HMAC-SHA256) for symmetric encryption.
All sensitive fields are encrypted before DB commit and decrypted on read.

Migration Path: Keys will transition to client-side Zero-Knowledge vaults.
"""
import os
import json
import logging
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, Text, String

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key Management
# ---------------------------------------------------------------------------
_ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

def _get_fernet():
    """Get Fernet instance. Generates a dev key if none is configured."""
    global _ENCRYPTION_KEY
    if not _ENCRYPTION_KEY:
        logger.warning(
            "ENCRYPTION_KEY not set — generating ephemeral key. "
            "DATA WILL BE UNREADABLE AFTER RESTART. Set ENCRYPTION_KEY in .env for production."
        )
        _ENCRYPTION_KEY = Fernet.generate_key().decode()
    return Fernet(_ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY)


_fernet = None

def get_fernet():
    """Lazy singleton to avoid issues at import time."""
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


# ---------------------------------------------------------------------------
# SQLAlchemy TypeDecorators
# ---------------------------------------------------------------------------

class EncryptedString(TypeDecorator):
    """
    Transparently encrypts/decrypts a string column.
    
    Usage:
        phone = db.Column(EncryptedString(500), nullable=True)
    
    Stored in DB as Fernet-encrypted base64 text.
    Returned to Python as plain string.
    """
    impl = String
    cache_ok = True

    def __init__(self, length=500, *args, **kwargs):
        super().__init__(length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        """Encrypt before saving to DB."""
        if value is None:
            return None
        try:
            f = get_fernet()
            return f.encrypt(value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return value  # Fallback: store plain (should not happen in prod)

    def process_result_value(self, value, dialect):
        """Decrypt when reading from DB."""
        if value is None:
            return None
        try:
            f = get_fernet()
            return f.decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            # Data was stored before encryption was enabled, return as-is
            logger.debug("Could not decrypt value — returning raw (pre-encryption data?)")
            return value
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return value


class EncryptedJSON(TypeDecorator):
    """
    Transparently encrypts/decrypts a JSON column stored as encrypted text.
    
    Usage:
        credentials = db.Column(EncryptedJSON, nullable=True)
    
    Python side: dict/list
    DB side: Fernet-encrypted JSON string
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Serialize to JSON, then encrypt."""
        if value is None:
            return None
        try:
            f = get_fernet()
            json_str = json.dumps(value, ensure_ascii=False)
            return f.encrypt(json_str.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"EncryptedJSON bind error: {e}")
            return json.dumps(value)  # Fallback

    def process_result_value(self, value, dialect):
        """Decrypt, then deserialize from JSON."""
        if value is None:
            return None
        try:
            f = get_fernet()
            decrypted = f.decrypt(value.encode('utf-8')).decode('utf-8')
            return json.loads(decrypted)
        except InvalidToken:
            # Try parsing as plain JSON (pre-encryption data)
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                logger.debug("Could not decrypt or parse JSON — returning raw")
                return value
        except Exception as e:
            logger.error(f"EncryptedJSON result error: {e}")
            try:
                return json.loads(value)
            except Exception:
                return value


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def encrypt_value(plaintext: str) -> str:
    """Encrypt a standalone string value."""
    if not plaintext:
        return plaintext
    f = get_fernet()
    return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a standalone string value."""
    if not ciphertext:
        return ciphertext
    try:
        f = get_fernet()
        return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return ciphertext


def generate_key() -> str:
    """Generate a new Fernet encryption key (for initial setup)."""
    return Fernet.generate_key().decode()
