import hashlib
import secrets

from cryptography.fernet import Fernet

from app.core.config import settings


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def encrypt_secret(secret: str) -> str:
    return Fernet(settings.effective_fernet_key.encode()).encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return Fernet(settings.effective_fernet_key.encode()).decrypt(value.encode("utf-8")).decode("utf-8")
