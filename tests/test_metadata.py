"""
Tests for metadata
"""

import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metadata import (
    save_metadata,
    get_metadata,
    delete_metadata,
    update_metadata,
    list_all,
    cleanup_expired,
)


def _make_record(file_id: str, expiry_days: int = None, auto_delete: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    expiry = (now + timedelta(days=expiry_days)).isoformat() if expiry_days else None
    return {
        "id": file_id,
        "original_name": "test.txt",
        "stored_name": file_id.replace("-", "") + ".sdf",
        "size": 1024,
        "upload_time": now.isoformat(),
        "expiry_time": expiry,
        "download_count": 0,
        "auto_delete": auto_delete,
        "encryption_key": "dummykey==",
        "note": "",
    }


@pytest.fixture(autouse=True)
def isolated_metadata(tmp_path, monkeypatch):
    """Redirect METADATA_FILE to a temp path for each test."""
    meta_file = tmp_path / "metadata.json"
    monkeypatch.setattr("metadata.METADATA_FILE", meta_file)
    monkeypatch.setattr("config.METADATA_FILE", meta_file)
    yield meta_file


class TestSaveAndGet:
    def test_save_and_retrieve(self):
        record = _make_record("ABCD-WXYZ-2345")
        save_metadata(record)
        retrieved = get_metadata("ABCD-WXYZ-2345")
        assert retrieved is not None
        assert retrieved["id"] == "ABCD-WXYZ-2345"

    def test_get_plain_id(self):
        """Should work with plain (no-dash) ID too."""
        record = _make_record("ABCD-WXYZ-2345")
        save_metadata(record)
        retrieved = get_metadata("ABCDWXYZ2345")
        assert retrieved is not None

    def test_get_nonexistent(self):
        result = get_metadata("XXXX-XXXX-XXXX")
        assert result is None


class TestDelete:
    def test_delete_existing(self):
        record = _make_record("ABCD-WXYZ-2345")
        save_metadata(record)
        result = delete_metadata("ABCD-WXYZ-2345")
        assert result is True
        assert get_metadata("ABCD-WXYZ-2345") is None

    def test_delete_nonexistent(self):
        result = delete_metadata("XXXX-XXXX-XXXX")
        assert result is False


class TestUpdate:
    def test_update_download_count(self):
        record = _make_record("ABCD-WXYZ-2345")
        save_metadata(record)
        update_metadata("ABCD-WXYZ-2345", {"download_count": 5})
        retrieved = get_metadata("ABCD-WXYZ-2345")
        assert retrieved["download_count"] == 5

    def test_update_nonexistent(self):
        result = update_metadata("XXXX-XXXX-XXXX", {"download_count": 1})
        assert result is False


class TestListAll:
    def test_list_multiple(self):
        save_metadata(_make_record("AAAA-BBBB-CCCC"))
        save_metadata(_make_record("DDDD-EEEE-FFFF"))
        records = list_all()
        assert len(records) == 2


class TestCleanupExpired:
    def test_removes_expired(self, monkeypatch, tmp_path):
        """Expired records should be removed."""
        # Create a record that expired 1 day ago
        past = datetime.now(timezone.utc) - timedelta(days=1)
        record = _make_record("ABCD-WXYZ-2345")
        record["expiry_time"] = past.isoformat()
        save_metadata(record)

        # Mock delete_stored_file to avoid actual file ops
        # Patch on the storage module (where it's defined), since metadata imports it lazily
        monkeypatch.setattr("storage.delete_stored_file", lambda x: True)

        removed = cleanup_expired()
        assert removed == 1
        assert get_metadata("ABCD-WXYZ-2345") is None

    def test_keeps_valid(self, monkeypatch):
        """Non-expired records should be kept."""
        future = datetime.now(timezone.utc) + timedelta(days=10)
        record = _make_record("ABCD-WXYZ-2345")
        record["expiry_time"] = future.isoformat()
        save_metadata(record)

        monkeypatch.setattr("storage.delete_stored_file", lambda x: True)

        removed = cleanup_expired()
        assert removed == 0
        assert get_metadata("ABCD-WXYZ-2345") is not None
