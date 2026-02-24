# Codes By Visionnn

import base64
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from logger import log


def generate_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded key string (safe to store in JSON metadata).
    """
    key = Fernet.generate_key()
    return key.decode("utf-8")


def _get_fernet(key_str: str) -> Fernet:
    """Instantiate a Fernet object from a base64 key string."""
    return Fernet(key_str.encode("utf-8"))


def encrypt_file(src_path: Path, dest_path: Path, key_str: str) -> None:
    """
    Encrypt a file and write the encrypted content to dest_path.

    Args:
        src_path:  Path to the plaintext source file.
        dest_path: Path where the encrypted file will be written.
        key_str:   Base64-encoded Fernet key string.

    Raises:
        FileNotFoundError: If src_path does not exist.
        OSError: On read/write errors.
    """
    fernet = _get_fernet(key_str)
    src_path = Path(src_path)
    dest_path = Path(dest_path)

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    log.debug(f"Encrypting '{src_path.name}' → '{dest_path.name}'")

    with open(src_path, "rb") as f:
        plaintext = f.read()

    ciphertext = fernet.encrypt(plaintext)

    with open(dest_path, "wb") as f:
        f.write(ciphertext)

    log.debug(f"Encryption complete. Encrypted size: {len(ciphertext):,} bytes")


def decrypt_file(src_path: Path, dest_path: Path, key_str: str) -> None:
    """
    Decrypt an encrypted file and write the plaintext to dest_path.

    Args:
        src_path:  Path to the encrypted source file.
        dest_path: Path where the decrypted file will be written.
        key_str:   Base64-encoded Fernet key string.

    Raises:
        InvalidToken: If the key is wrong or the file is corrupted.
        FileNotFoundError: If src_path does not exist.
        OSError: On read/write errors.
    """
    fernet = _get_fernet(key_str)
    src_path = Path(src_path)
    dest_path = Path(dest_path)

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    log.debug(f"Decrypting '{src_path.name}' → '{dest_path.name}'")

    with open(src_path, "rb") as f:
        ciphertext = f.read()

    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken:
        log.error(f"Decryption failed for '{src_path.name}': invalid key or corrupted file.")
        raise

    with open(dest_path, "wb") as f:
        f.write(plaintext)

    log.debug(f"Decryption complete. Decrypted size: {len(plaintext):,} bytes")

