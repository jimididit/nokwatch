"""Encryption for auth credentials and notification config stored in the database."""
import logging
from typing import Optional

from core.config import Config

logger = logging.getLogger(__name__)

_fernet = None


def _get_fernet():
    """Lazy-init Fernet instance from ENCRYPTION_KEY. Returns None if key not set."""
    global _fernet
    if _fernet is not None:
        return _fernet
    key = (getattr(Config, "ENCRYPTION_KEY", None) or "").strip()
    if not key:
        _fernet = False  # Mark as checked
        return None
    try:
        from cryptography.fernet import Fernet, InvalidToken
        f = Fernet(key.encode() if isinstance(key, str) else key)
        _fernet = f
        return f
    except Exception as e:
        logger.warning("Invalid ENCRYPTION_KEY; credentials will not be encrypted: %s", e)
        _fernet = False
        return None


def encrypt_credentials(plaintext: str) -> str:
    """
    Encrypt a string for storage. If ENCRYPTION_KEY is not set, returns plaintext unchanged.
    Caller should pass JSON or other string; we do not handle None (caller uses None for empty).
    """
    if not plaintext:
        return plaintext
    f = _get_fernet()
    if not f:
        return plaintext
    try:
        return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.warning("Encryption failed; storing plaintext: %s", e)
        return plaintext


def decrypt_credentials(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypt a stored string. If ENCRYPTION_KEY is not set or value is legacy plaintext,
    returns the value unchanged. Returns None for None or empty input.
    """
    if ciphertext is None or (isinstance(ciphertext, str) and not ciphertext.strip()):
        return None
    s = ciphertext if isinstance(ciphertext, str) else str(ciphertext)
    f = _get_fernet()
    if not f:
        return s
    try:
        return f.decrypt(s.encode("utf-8")).decode("utf-8")
    except Exception:
        # Legacy plaintext or corrupted; return as-is so existing data still works
        return s


def _reset_for_tests():
    """Reset the cached Fernet instance. For use in tests only."""
    global _fernet
    _fernet = None
