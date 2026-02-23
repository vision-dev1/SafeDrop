# Codes By Visionnn

import os
import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken

from crypto import generate_key, encrypt_file, decrypt_file


def _make_temp_file(content: bytes, suffix: str = ".bin") -> Path:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return Path(path)


class TestGenerateKey:
    def test_returns_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_unique_keys(self):
        keys = {generate_key() for _ in range(100)}
        assert len(keys) == 100

    def test_valid_fernet_key(self):
        """Key should be usable by Fernet without error."""
        from cryptography.fernet import Fernet
        key = generate_key()
        fernet = Fernet(key.encode("utf-8"))
        assert fernet is not None


class TestEncryptDecryptRoundtrip:
    def test_roundtrip_small_file(self, tmp_path):
        content = b"Hello, SafeDrop! This is a test file."
        src = _make_temp_file(content)
        enc = tmp_path / "encrypted.sdf"
        dec = tmp_path / "decrypted.txt"
        key = generate_key()

        try:
            encrypt_file(src, enc, key)
            assert enc.exists()
            assert enc.read_bytes() != content  # Must be different (encrypted)

            decrypt_file(enc, dec, key)
            assert dec.read_bytes() == content
        finally:
            src.unlink(missing_ok=True)

    def test_roundtrip_large_file(self, tmp_path):
        """Test with a 5 MB file."""
        content = os.urandom(5 * 1024 * 1024)
        src = _make_temp_file(content)
        enc = tmp_path / "encrypted.sdf"
        dec = tmp_path / "decrypted.bin"
        key = generate_key()

        try:
            encrypt_file(src, enc, key)
            decrypt_file(enc, dec, key)
            assert dec.read_bytes() == content
        finally:
            src.unlink(missing_ok=True)

    def test_wrong_key_raises(self, tmp_path):
        """Decrypting with the wrong key should raise InvalidToken."""
        content = b"Secret data"
        src = _make_temp_file(content)
        enc = tmp_path / "encrypted.sdf"
        dec = tmp_path / "decrypted.txt"
        key1 = generate_key()
        key2 = generate_key()

        try:
            encrypt_file(src, enc, key1)
            with pytest.raises(InvalidToken):
                decrypt_file(enc, dec, key2)
        finally:
            src.unlink(missing_ok=True)

    def test_empty_file_roundtrip(self, tmp_path):
        """Empty files should encrypt and decrypt correctly."""
        content = b""
        src = _make_temp_file(content)
        enc = tmp_path / "encrypted.sdf"
        dec = tmp_path / "decrypted.txt"
        key = generate_key()

        try:
            encrypt_file(src, enc, key)
            decrypt_file(enc, dec, key)
            assert dec.read_bytes() == content
        finally:
            src.unlink(missing_ok=True)

