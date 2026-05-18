import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


ENCRYPTED_VALUE_PREFIX = "enc:v1:"


def _get_fernet():
    secret = os.getenv("MOODLE_CONFIG_ENCRYPTION_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("MOODLE_CONFIG_ENCRYPTION_KEY is required to encrypt Moodle config")

    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_config_secret(value):
    if value is None:
        return None

    value = str(value)
    if value.startswith(ENCRYPTED_VALUE_PREFIX):
        return value

    token = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_VALUE_PREFIX}{token}"


def decrypt_config_secret(value):
    if value is None:
        return None

    value = str(value)
    if not value.startswith(ENCRYPTED_VALUE_PREFIX):
        return value

    token = value[len(ENCRYPTED_VALUE_PREFIX):]
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("could not decrypt Moodle config password") from exc
