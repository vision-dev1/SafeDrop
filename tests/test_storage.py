"""
Tests for storage
Focuses on directory traversal prevention and store/retrieve roundtrip.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from crypto import generate_key
from storage import store_file, retrieve_file, delete_stored_file, get_storage_path


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect STORAGE_DIR to a temp directory for each test."""
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setattr("storage.STORAGE_DIR", storage)
    yield storage


def _make_temp_file(content: bytes, suffix: str = ".txt") -> Path:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return Path(path)


class TestStoreAndRetrieve:
    def test_roundtrip(self, tmp_path):
        content = b"SafeDrop storage roundtrip test content."
        src = _make_temp_file(content)
        key = generate_key()
        file_id = "ABCD-WXYZ-2345"

        try:
            store_file(src, file_id, key)
            dest = retrieve_file(file_id, tmp_path / "out", "restored.txt", key)
            assert dest.read_bytes() == content
        finally:
            src.unlink(missing_ok=True)

    def test_stored_file_is_encrypted(self, tmp_path):
        """Stored file should not contain plaintext content."""
        content = b"This is plaintext that should not appear in storage."
        src = _make_temp_file(content)
        key = generate_key()
        file_id = "ABCD-WXYZ-2345"

        try:
            store_file(src, file_id, key)
            stored = get_storage_path(file_id)
            assert stored is not None
            stored_bytes = stored.read_bytes()
            assert content not in stored_bytes
        finally:
            src.unlink(missing_ok=True)

    def test_filename_collision_handled(self, tmp_path):
        """If output file already exists, a new name should be generated."""
        content = b"Collision test"
        src = _make_temp_file(content)
        key = generate_key()
        file_id = "ABCD-WXYZ-2345"
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        # Pre-create the expected output file
        (out_dir / "restored.txt").write_bytes(b"existing file")

        try:
            store_file(src, file_id, key)
            dest = retrieve_file(file_id, out_dir, "restored.txt", key)
            # Should have been renamed
            assert dest.name != "restored.txt"
            assert dest.read_bytes() == content
        finally:
            src.unlink(missing_ok=True)


class TestDirectoryTraversal:
    def test_traversal_in_file_id_rejected(self):
        """File IDs containing path traversal sequences should be rejected."""
        with pytest.raises(ValueError, match="traversal"):
            from storage import _safe_storage_path
            _safe_storage_path("../../etc/passwd")

    def test_traversal_with_dotdot(self):
        with pytest.raises(ValueError, match="traversal"):
            from storage import _safe_storage_path
            _safe_storage_path("../../../windows/system32/cmd")


class TestDeleteStoredFile:
    def test_delete_existing(self, tmp_path):
        content = b"Delete me"
        src = _make_temp_file(content)
        key = generate_key()
        file_id = "ABCD-WXYZ-2345"

        try:
            store_file(src, file_id, key)
            assert get_storage_path(file_id) is not None
            result = delete_stored_file(file_id)
            assert result is True
            assert get_storage_path(file_id) is None
        finally:
            src.unlink(missing_ok=True)

    def test_delete_nonexistent(self):
        result = delete_stored_file("XXXX-XXXX-XXXX")
        assert result is False
