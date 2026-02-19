# Codes By Vision

"""
SafeDrop Metadata Manager
Manages the JSON metadata store for all uploaded files.

Schema per file record:
{
    "id":               str,   # Unique file ID (dashed format)
    "original_name":    str,   # Original filename
    "stored_name":      str,   # Filename in storage (id-based)
    "size":             int,   # Original file size in bytes
    "upload_time":      str,   # ISO 8601 timestamp
    "expiry_time":      str,   # ISO 8601 timestamp (or null)
    "download_count":   int,   # Number of times downloaded
    "auto_delete":      bool,  # Delete after first download?
    "encryption_key":   str,   # Base64 Fernet key
    "note":             str,   # Optional uploader note
}
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from config import METADATA_FILE
from logger import log

# Thread lock for safe concurrent access
_lock = threading.Lock()


def _load() -> Dict[str, dict]:
    """Load the metadata JSON file. Returns empty dict if not found."""
    if not METADATA_FILE.exists():
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.error(f"Failed to load metadata: {e}")
        return {}


def _save(data: Dict[str, dict]) -> None:
    """Persist the metadata dict to disk."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        log.error(f"Failed to save metadata: {e}")
        raise


def save_metadata(record: dict) -> None:
    """Add or update a file record in the metadata store."""
    with _lock:
        data = _load()
        file_id = record["id"].replace("-", "")
        data[file_id] = record
        _save(data)
        log.debug(f"Metadata saved for ID: {record['id']}")


def get_metadata(file_id: str) -> Optional[dict]:
    """
    Retrieve a file record by ID.

    Accepts both dashed (XXXX-XXXX-XXXX) and plain (XXXXXXXXXXXX) formats.
    Returns None if not found.
    """
    key = file_id.replace("-", "").upper()
    with _lock:
        data = _load()
        return data.get(key)


def delete_metadata(file_id: str) -> bool:
    """
    Remove a file record from the metadata store.

    Returns True if the record was found and deleted, False otherwise.
    """
    key = file_id.replace("-", "").upper()
    with _lock:
        data = _load()
        if key in data:
            del data[key]
            _save(data)
            log.debug(f"Metadata deleted for ID: {file_id}")
            return True
        return False


def update_metadata(file_id: str, updates: dict) -> bool:
    """
    Apply partial updates to an existing file record.

    Returns True if the record was found and updated.
    """
    key = file_id.replace("-", "").upper()
    with _lock:
        data = _load()
        if key not in data:
            return False
        data[key].update(updates)
        _save(data)
        return True


def list_all() -> List[dict]:
    """Return all file records as a list."""
    with _lock:
        data = _load()
        return list(data.values())


def cleanup_expired() -> int:
    """
    Remove all expired file records from metadata.
    Returns the number of records removed.

    Note: This only removes metadata. Storage files are deleted by storage.py.
    """
    from storage import delete_stored_file

    now = datetime.now(timezone.utc)
    removed = 0

    with _lock:
        data = _load()
        expired_keys = []

        for key, record in data.items():
            expiry_str = record.get("expiry_time")
            if expiry_str:
                try:
                    expiry = datetime.fromisoformat(expiry_str)
                    if expiry <= now:
                        expired_keys.append(key)
                except ValueError:
                    pass

        for key in expired_keys:
            record = data[key]
            file_id = record["id"]
            # Delete the stored (encrypted) file
            delete_stored_file(file_id)
            del data[key]
            removed += 1
            log.info(f"Expired file removed: {record.get('original_name', '?')} (ID: {file_id})")

        if removed:
            _save(data)

    return removed

