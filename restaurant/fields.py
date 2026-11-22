from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

PREFIX = "enc1:"


@lru_cache(maxsize=2)
def _fernet_for(key):
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY is not a valid key.") from exc


def _fernet():
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY is not set in the .env file.")
    return _fernet_for(key)


def encrypt_value(value):
    if value is None or value == "":
        return value
    token = _fernet().encrypt(str(value).encode("utf-8")).decode("ascii")
    return PREFIX + token


def decrypt_value(value):
    if value is None or value == "":
        return value
    if not value.startswith(PREFIX):
        # Older, not-yet-encrypted data. It is encrypted the next time the row is saved.
        return value
    try:
        return _fernet().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ImproperlyConfigured(
            "Could not decrypt data. FIELD_ENCRYPTION_KEY is missing or different from the key used to encrypt it."
        ) from exc


class EncryptedCharField(models.CharField):
    """Single-line text, stored encrypted. max_length applies to the readable text."""

    def db_type(self, connection):
        return "text"

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(super().get_prep_value(value))


class EncryptedTextField(models.TextField):
    """Multi-line text, stored encrypted."""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(super().get_prep_value(value))