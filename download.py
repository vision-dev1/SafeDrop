# Codes By Visionnn

from datetime import datetime, timezone
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from cli import (
    console,
    print_section,
    print_error,
    print_warning,
    print_info,
    print_download_result,
    prompt_file_id,
    prompt_download_dir,
    COLOR_PRIMARY,
    COLOR_DIM,
    COLOR_WARNING,
)
from id_generator import is_valid_id_format, normalize_id
from logger import log
from metadata import get_metadata, update_metadata, delete_metadata
from storage import retrieve_file, delete_stored_file


def run_download() -> None:
    """Run the interactive download flow."""
    print_section("Download File")

    # ── Step 1: Get file ID ───────────────────────────────────────────────────
    raw_id = prompt_file_id()

    if not raw_id:
        print_error("No ID provided.")
        return

    # ── Step 2: Validate ID format ────────────────────────────────────────────
    if not is_valid_id_format(raw_id):
        print_error(
            f"Invalid file ID format: '{raw_id}'\n"
            "  Expected format: XXXX-XXXX-XXXX (12 alphanumeric characters)"
        )
        return

    file_id = normalize_id(raw_id)

    # ── Step 3: Look up metadata ──────────────────────────────────────────────
    record = get_metadata(file_id)

    if record is None:
        print_error(f"File not found. ID '{file_id}' does not exist.")
        log.warning(f"DOWNLOAD FAILED | id='{file_id}' reason='not found'")
        return

    # ── Step 4: Check expiry ──────────────────────────────────────────────────
    expiry_str = record.get("expiry_time")
    if expiry_str:
        try:
            expiry = datetime.fromisoformat(expiry_str)
            if datetime.now(timezone.utc) > expiry:
                print_error(
                    f"This file has expired and is no longer available.\n"
                    f"  Expired at: {expiry.strftime('%Y-%m-%d %H:%M UTC')}"
                )
                log.info(f"DOWNLOAD BLOCKED | id='{file_id}' reason='expired'")
                # Clean up expired file
                delete_stored_file(file_id)
                delete_metadata(file_id)
                return
        except ValueError:
            pass  # Malformed expiry — proceed anyway

    # ── Step 5: Show file info ────────────────────────────────────────────────
    original_name = record.get("original_name", "unknown")
    file_size = record.get("size", 0)
    download_count = record.get("download_count", 0)
    note = record.get("note", "")
    auto_delete = record.get("auto_delete", False)

    console.print(f"\n  [{COLOR_DIM}]File:[/{COLOR_DIM}] [{COLOR_PRIMARY}]{original_name}[/{COLOR_PRIMARY}]")
    console.print(f"  [{COLOR_DIM}]Size:[/{COLOR_DIM}] {_format_size(file_size)}")
    console.print(f"  [{COLOR_DIM}]Downloads so far:[/{COLOR_DIM}] {download_count}")
    if note:
        console.print(f"  [{COLOR_DIM}]Note:[/{COLOR_DIM}] {note}")
    if auto_delete:
        console.print(
            f"\n  [{COLOR_WARNING}]⚠ This file will be deleted after download.[/{COLOR_WARNING}]"
        )

    # ── Step 6: Get destination directory ────────────────────────────────────
    dest_dir = prompt_download_dir()

    # ── Step 7: Decrypt and restore ──────────────────────────────────────────
    encryption_key = record.get("encryption_key")
    if not encryption_key:
        print_error("File record is corrupted (missing encryption key).")
        log.error(f"DOWNLOAD ERROR | id='{file_id}' reason='missing encryption key'")
        return

    with Progress(
        SpinnerColumn(spinner_name="dots", style=f"bold {COLOR_PRIMARY}"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Decrypting and restoring file...", total=None)
        try:
            dest_path = retrieve_file(
                file_id=file_id,
                dest_dir=dest_dir,
                original_name=original_name,
                encryption_key=encryption_key,
            )
        except FileNotFoundError:
            print_error("Stored file is missing. It may have been deleted or expired.")
            log.error(f"DOWNLOAD ERROR | id='{file_id}' reason='stored file missing'")
            return
        except Exception as e:
            print_error(f"Failed to retrieve file: {e}")
            log.error(f"DOWNLOAD ERROR | id='{file_id}' error='{e}'")
            return

    # ── Step 8: Update download counter ──────────────────────────────────────
    new_count = download_count + 1
    update_metadata(file_id, {"download_count": new_count})

    log.info(
        f"DOWNLOAD | file='{original_name}' id='{file_id}' "
        f"dest='{dest_path}' download_count={new_count}"
    )

    # ── Step 9: Handle auto-delete ────────────────────────────────────────────
    if auto_delete:
        delete_stored_file(file_id)
        delete_metadata(file_id)
        log.info(f"AUTO-DELETE | id='{file_id}' file='{original_name}'")
        console.print(
            f"\n  [{COLOR_DIM}]File has been deleted from SafeDrop storage (auto-delete).[/{COLOR_DIM}]"
        )

    # ── Step 10: Show result ──────────────────────────────────────────────────
    print_download_result(
        dest_path=dest_path,
        original_name=original_name,
        size=file_size,
        download_count=new_count,
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

