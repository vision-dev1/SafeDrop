"""
SafeDrop Upload Flow
Orchestrates the complete file upload process:
  1. Prompt for file path
  2. Validate file (size, existence)
  3. Security scan
  4. Prompt for options (expiry, auto-delete, note)
  5. Encrypt and store
  6. Save metadata
  7. Display file ID
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config
from cli import (
    console,
    print_section,
    print_error,
    print_warning,
    print_info,
    print_security_warning,
    print_file_id_card,
    prompt_file_path,
    prompt_expiry_days,
    prompt_auto_delete,
    prompt_note,
    COLOR_PRIMARY,
    COLOR_DIM,
    COLOR_WARNING,
)
from crypto import generate_key
from id_generator import generate_id
from logger import log
from metadata import save_metadata, get_metadata
from security import scan_file
from storage import store_file


def run_upload() -> None:
    """Run the interactive upload flow."""
    print_section("Upload File")

    # ── Step 1: Get file path ─────────────────────────────────────────────────
    filepath = prompt_file_path()

    # ── Step 2: Validate file size ────────────────────────────────────────────
    try:
        file_size = filepath.stat().st_size
    except OSError as e:
        print_error(f"Cannot read file: {e}")
        return

    if file_size == 0:
        print_error("File is empty. Cannot upload an empty file.")
        return

    if file_size > config.MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        print_error(
            f"File too large: {size_mb:.1f} MB "
            f"(limit is {config.MAX_FILE_SIZE_MB} MB)"
        )
        return

    print_info(f"File: {filepath.name}  ({_format_size(file_size)})")

    # ── Step 3: Security scan ─────────────────────────────────────────────────
    console.print(f"\n  [{COLOR_DIM}]Running security scan...[/{COLOR_DIM}]")

    with Progress(
        SpinnerColumn(spinner_name="dots", style=f"bold {COLOR_PRIMARY}"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning file for threats...", total=None)
        is_safe, reason = scan_file(filepath)

    if not is_safe:
        print_security_warning(reason)
        log.warning(f"Upload blocked for '{filepath.name}': {reason}")
        return

    console.print(f"  [{COLOR_PRIMARY}]✓ Security scan passed[/{COLOR_PRIMARY}]")

    # ── Step 4: Upload options ────────────────────────────────────────────────
    expiry_days = prompt_expiry_days(default=config.DEFAULT_EXPIRY_DAYS)
    auto_delete = prompt_auto_delete()
    note = prompt_note()

    # ── Step 5: Generate ID and encrypt ──────────────────────────────────────
    file_id = generate_id()
    encryption_key = generate_key()

    upload_time = datetime.now(timezone.utc)
    expiry_time = (
        upload_time + timedelta(days=expiry_days) if expiry_days else None
    )

    with Progress(
        SpinnerColumn(spinner_name="dots", style=f"bold {COLOR_PRIMARY}"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style=COLOR_PRIMARY),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Encrypting and storing file...", total=None)
        try:
            store_file(filepath, file_id, encryption_key)
        except Exception as e:
            print_error(f"Failed to store file: {e}")
            log.error(f"Storage error for '{filepath.name}': {e}")
            return

    # ── Step 6: Save metadata ─────────────────────────────────────────────────
    record = {
        "id":             file_id,
        "original_name":  filepath.name,
        "stored_name":    file_id.replace("-", "") + ".sdf",
        "size":           file_size,
        "upload_time":    upload_time.isoformat(),
        "expiry_time":    expiry_time.isoformat() if expiry_time else None,
        "download_count": 0,
        "auto_delete":    auto_delete,
        "encryption_key": encryption_key,
        "note":           note,
    }

    try:
        save_metadata(record)
    except Exception as e:
        print_error(f"Failed to save metadata: {e}")
        log.error(f"Metadata save error: {e}")
        return

    log.info(
        f"UPLOAD | file='{filepath.name}' id='{file_id}' "
        f"size={file_size} expiry='{expiry_time}' auto_delete={auto_delete}"
    )

    # ── Step 7: Show result ───────────────────────────────────────────────────
    print_file_id_card(
        file_id=file_id,
        filename=filepath.name,
        size=file_size,
        expiry_days=expiry_days,
        auto_delete=auto_delete,
    )


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.2f} GB"
