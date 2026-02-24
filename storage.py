# Codes By Visionnn

"""
SafeDrop Storage Manager
Handles secure file storage: encrypting files on upload and decrypting on download.
Prevents directory traversal attacks by validating all paths stay within STORAGE_DIR.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from config import STORAGE_DIR
from crypto import encrypt_file, decrypt_file
from logger import log


def _init_storage() -> None:
    """Ensure the storage directory exists with restricted permissions."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    # On Unix-like systems, restrict directory to owner only
    try:
        os.chmod(STORAGE_DIR, 0o700)
    except (AttributeError, NotImplementedError):
        pass  # Windows doesn't support chmod the same way


def flatten_storage() -> int:
    """
    Ensure all stored files live directly inside STORAGE_DIR with no nesting.

    Scans STORAGE_DIR for any subdirectories. For each one found, every file
    inside it (at any depth) is moved up to STORAGE_DIR. If a filename
    collision occurs the incoming file is renamed with a numeric suffix.
    After all files are relocated the now-empty subdirectory tree is removed.

    Returns:
        The number of files that were relocated.
    """
    _init_storage()
    storage_root = STORAGE_DIR.resolve()
    relocated = 0

    # Collect all immediate child subdirectories (non-recursive at top level
    # so we can rmtree each one cleanly after draining it).
    subdirs = [p for p in storage_root.iterdir() if p.is_dir()]

    for subdir in subdirs:
        # Walk the entire subtree of this nested directory.
        for nested_file in list(subdir.rglob("*")):
            if not nested_file.is_file():
                continue

            dest = storage_root / nested_file.name

            # Resolve filename collision: append _1, _2, … until unique.
            if dest.exists():
                stem = nested_file.stem
                suffix = nested_file.suffix
                counter = 1
                while dest.exists():
                    dest = storage_root / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.move(str(nested_file), str(dest))
            log.info(
                f"flatten_storage: moved '{nested_file}' → '{dest.name}'"
            )
            relocated += 1

        # Remove the now-empty subdirectory tree.
        try:
            shutil.rmtree(subdir)
            log.info(f"flatten_storage: removed nested directory '{subdir}'")
        except OSError as e:
            log.warning(f"flatten_storage: could not remove '{subdir}': {e}")

    if relocated:
        log.info(
            f"flatten_storage: relocated {relocated} file(s) to '{storage_root}'."
        )

    return relocated


def _safe_storage_path(file_id: str) -> Path:
    """
    Compute the storage path for a file ID and verify it stays within STORAGE_DIR.
    Raises ValueError on directory traversal attempts.
    """
    _init_storage()
    stored_name = file_id.replace("-", "") + ".sdf"  # SafeDrop File extension
    candidate = (STORAGE_DIR / stored_name).resolve()

    # Prevent directory traversal
    if not str(candidate).startswith(str(STORAGE_DIR.resolve())):
        raise ValueError(f"Directory traversal detected for ID: {file_id}")

    return candidate


def store_file(src_path: Path, file_id: str, encryption_key: str) -> Path:
    """
    Encrypt and store a file in the SafeDrop storage directory.

    Args:
        src_path:       Path to the source file.
        file_id:        The unique file ID (used to name the stored file).
        encryption_key: Base64 Fernet key string.

    Returns:
        Path to the stored encrypted file.
    """
    _init_storage()
    dest_path = _safe_storage_path(file_id)

    log.info(f"Storing file '{src_path.name}' as '{dest_path.name}'")
    encrypt_file(Path(src_path), dest_path, encryption_key)
    log.info(f"File stored successfully: {dest_path}")

    return dest_path


def retrieve_file(file_id: str, dest_dir: Path, original_name: str, encryption_key: str) -> Path:
    """
    Decrypt and restore a stored file to the destination directory.

    Args:
        file_id:         The unique file ID.
        dest_dir:        Directory where the file will be restored.
        original_name:   The original filename to restore as.
        encryption_key:  Base64 Fernet key string.

    Returns:
        Path to the restored (decrypted) file.

    Raises:
        FileNotFoundError: If the stored file doesn't exist.
        ValueError: On directory traversal in dest_dir.
    """
    stored_path = _safe_storage_path(file_id)

    if not stored_path.exists():
        raise FileNotFoundError(f"Stored file not found for ID: {file_id}")

    dest_dir = Path(dest_dir).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize original_name to prevent traversal in output path
    safe_name = Path(original_name).name  # Strip any directory components
    if not safe_name:
        safe_name = "safedrop_file"

    dest_path = dest_dir / safe_name

    # Handle filename collisions
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    log.info(f"Retrieving file ID '{file_id}' → '{dest_path}'")
    decrypt_file(stored_path, dest_path, encryption_key)
    log.info(f"File retrieved successfully: {dest_path}")

    return dest_path


def delete_stored_file(file_id: str) -> bool:
    """
    Delete a stored encrypted file.

    Returns True if deleted, False if not found.
    """
    try:
        stored_path = _safe_storage_path(file_id)
    except ValueError:
        return False

    if stored_path.exists():
        stored_path.unlink()
        log.info(f"Stored file deleted for ID: {file_id}")
        return True

    return False


def get_storage_path(file_id: str) -> Optional[Path]:
    """Return the storage path for a file ID, or None if it doesn't exist."""
    try:
        path = _safe_storage_path(file_id)
        return path if path.exists() else None
    except ValueError:
        return None


def get_stored_size(file_id: str) -> Optional[int]:
    """Return the size of the stored (encrypted) file in bytes, or None."""
    path = get_storage_path(file_id)
    if path:
        return path.stat().st_size
    return None

