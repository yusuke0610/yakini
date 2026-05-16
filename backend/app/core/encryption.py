import os

from cryptography.fernet import Fernet

from . import env_keys


def _get_fernet() -> Fernet:
    key = os.getenv(env_keys.FIELD_ENCRYPTION_KEY, "").strip()
    if not key:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not configured")
    return Fernet(key.encode())


def encrypt_field(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()
