import base64
import hashlib
import hmac

import sqlalchemy as sa
from cryptography.fernet import Fernet
from flask import current_app

# Valid Fernet key used only when the app runs under tests with no key set
_TEST_KEY = base64.urlsafe_b64encode(b"0" * 32).decode()


def _key():
    key = current_app.config.get("PII_ENCRYPTION_KEY")
    if key:
        return key
    if current_app.testing:
        return _TEST_KEY
    raise RuntimeError("PII_ENCRYPTION_KEY is not set")


def encrypt(value):
    return Fernet(_key()).encrypt(value.encode()).decode()


def decrypt(token):
    return Fernet(_key()).decrypt(token.encode()).decode()


def blind_index(value):
    """Deterministic keyed hash, used for lookup and uniqueness only."""
    secret = hashlib.sha256(b"blind-index:" + _key().encode()).digest()
    return hmac.new(secret, value.strip().encode(), hashlib.sha256).hexdigest()


class EncryptedString(sa.TypeDecorator):
    """Stores text encrypted; reads back as plaintext."""
    impl = sa.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt(value)