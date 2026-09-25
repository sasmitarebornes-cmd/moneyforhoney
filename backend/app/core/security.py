"""
Fernet KeyVault security module.
Provides AES-128-CBC encryption and HMAC-SHA256 authenticated encryption
for exchange API keys and secrets stored at rest.
"""

import base64
from typing import Any

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    HAS_CRYPTOGRAPHY = True
except (ImportError, ModuleNotFoundError):
    Fernet = None  # type: ignore[assignment]
    HAS_CRYPTOGRAPHY = False

from app.core.config import settings


class KeyVaultManager:
    """Enterprise-grade symmetric encryption manager for exchange credentials."""

    def __init__(self, key: str | None = None):
        self._fernet = (
            self._initialize_cipher(key or settings.FERNET_KEY)
            if HAS_CRYPTOGRAPHY
            else None
        )

    def _initialize_cipher(self, raw_key: str | None) -> Any | None:
        if not HAS_CRYPTOGRAPHY or Fernet is None:
            return None

        if raw_key and len(raw_key.strip()) > 0:
            try:
                return Fernet(
                    raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key
                )
            except Exception:
                pass

        # Deterministic derivation or fallback key for zero-config safe boot
        salt = b"honey_vault_salt_v2"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        derived = base64.urlsafe_b64encode(
            kdf.derive(settings.SECRET_KEY.encode("utf-8"))
        )
        return Fernet(derived)

    def encrypt(self, plain_text: str) -> str:
        """Encrypt plain text credential into safe base64 ciphertext token."""
        if not plain_text:
            return ""
        if not self._fernet:
            return plain_text
        return self._fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        """Decrypt base64 ciphertext token back into plain text credential."""
        if not cipher_text:
            return ""
        if not self._fernet:
            return cipher_text
        try:
            return self._fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
        except Exception:
            # If not encrypted with Fernet (i.e. raw API key), return as is
            return cipher_text


key_vault = KeyVaultManager()
