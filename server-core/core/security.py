import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet

from .config import ENCRYPTED_DIR, KEY_PATH, ensure_data_dirs


def _fernet_key_from_local_secret(secret: bytes) -> bytes:
    digest = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher() -> Fernet:
    ensure_data_dirs()
    if KEY_PATH.exists():
        secret = KEY_PATH.read_bytes()
    else:
        secret = os.urandom(32)
        KEY_PATH.write_bytes(secret)
    return Fernet(_fernet_key_from_local_secret(secret))


def encrypt_bytes(data: bytes) -> bytes:
    return get_cipher().encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    return get_cipher().decrypt(data)


def encrypted_project_path(project_id: int, filename: str) -> Path:
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in filename)
    directory = ENCRYPTED_DIR / str(project_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{safe_name}.enc"
