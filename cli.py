"""
SafeDrop CLI Interface
Renders the banner, menus, and styled terminal output using Rich.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from config import APP_NAME, APP_VERSION, APP_AUTHOR, APP_TAGLINE

console = Console()

# ─── Color Palette ────────────────────────────────────────────────────────────
COLOR_PRIMARY   = "bright_cyan"
COLOR_SUCCESS   = "bright_green"
COLOR_WARNING   = "bright_yellow"
COLOR_ERROR     = "bright_red"
COLOR_DIM       = "dim white"
COLOR_ACCENT    = "magenta"
COLOR_HIGHLIGHT = "bold bright_white"


BANNER = r"""
  ____         __       ____
 / __/__ _____/ /__ ___/ / /______  ___
_\ \/ _ `/ _  / -_) _  / __/ __/ \/ _ \
/___/\_,_/\_,_/\__/\_,_/\__/_/  /_/ .__/
                                  /_/
"""


def print_banner() -> None:
    """Print the SafeDrop ASCII art banner with version and author info."""
    console.print()

    banner_text = Text(BANNER, style=f"bold {COLOR_PRIMARY}")
    console.print(Align.center(banner_text))

    subtitle = Text(f"  {APP_TAGLINE}", style=f"italic {COLOR_DIM}")
    console.print(Align.center(subtitle))

    info_line = Text(
        f"  v{APP_VERSION}  ·  Developed by {APP_AUTHOR}",
        style=f"dim {COLOR_ACCENT}",
    )
    console.print(Align.center(info_line))
    console.print()
    console.print(Rule(style=f"dim {COLOR_PRIMARY}"))
    console.print()


def print_main_menu() -> None:
    """Print the main menu options."""
    table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Key", style=f"bold {COLOR_PRIMARY}", width=4)
    table.add_column("Action", style=COLOR_HIGHLIGHT)
    table.add_column("Description", style=COLOR_DIM)

    table.add_row("  1", "Upload File",   "Securely upload and share a file")
    table.add_row("  2", "Download File", "Retrieve a file using its unique ID")
    table.add_row("  3", "Exit",          "Quit SafeDrop")

    console.print(Align.center(table))
    console.print()


def prompt_menu_choice() -> str:
    """Prompt the user to select a menu option."""
    return Prompt.ask(
        f"[{COLOR_PRIMARY}]Select an option[/{COLOR_PRIMARY}]",
        choices=["1", "2", "3"],
        show_choices=True,
    )


def prompt_file_path() -> Path:
    """Prompt for a file path and validate it exists."""
    while True:
        raw = Prompt.ask(f"\n[{COLOR_PRIMARY}]Enter file path[/{COLOR_PRIMARY}]")
        path = Path(raw.strip().strip('"').strip("'"))
        if not path.exists():
            print_error(f"File not found: {path}")
            continue
        if path.is_dir():
            print_error("Path points to a directory, not a file.")
            continue
        return path


def prompt_file_id() -> str:
    """Prompt for a file ID."""
    return Prompt.ask(f"\n[{COLOR_PRIMARY}]Enter file ID[/{COLOR_PRIMARY}]").strip()


def prompt_download_dir() -> Path:
    """Prompt for a download destination directory."""
    default = str(Path.home() / "Downloads")
    raw = Prompt.ask(
        f"[{COLOR_PRIMARY}]Save to directory[/{COLOR_PRIMARY}]",
        default=default,
    )
    return Path(raw.strip().strip('"').strip("'"))


def prompt_expiry_days(default: int = 7) -> Optional[int]:
    """Prompt for file expiry in days. 0 = never expires."""
    console.print(
        f"  [{COLOR_DIM}]File expiry: how many days until this file is automatically deleted?[/{COLOR_DIM}]"
    )
    console.print(f"  [{COLOR_DIM}]Enter 0 for no expiry.[/{COLOR_DIM}]")
    days = IntPrompt.ask(
        f"[{COLOR_PRIMARY}]Expiry days[/{COLOR_PRIMARY}]",
        default=default,
    )
    return days if days > 0 else None


def prompt_auto_delete() -> bool:
    """Prompt whether to auto-delete the file after first download."""
    return Confirm.ask(
        f"[{COLOR_PRIMARY}]Auto-delete after first download?[/{COLOR_PRIMARY}]",
        default=False,
    )


def prompt_note() -> str:
    """Prompt for an optional note about the file."""
    return Prompt.ask(
        f"[{COLOR_PRIMARY}]Add a note (optional)[/{COLOR_PRIMARY}]",
        default="",
    )


def print_success(message: str) -> None:
    console.print(f"\n  [{COLOR_SUCCESS}]✓ {message}[/{COLOR_SUCCESS}]")


def print_error(message: str) -> None:
    console.print(f"\n  [{COLOR_ERROR}]✗ {message}[/{COLOR_ERROR}]")


def print_warning(message: str) -> None:
    console.print(f"\n  [{COLOR_WARNING}]⚠ {message}[/{COLOR_WARNING}]")


def print_info(message: str) -> None:
    console.print(f"  [{COLOR_DIM}]→ {message}[/{COLOR_DIM}]")


def print_section(title: str) -> None:
    console.print()
    console.print(Rule(f"[bold {COLOR_PRIMARY}]{title}[/bold {COLOR_PRIMARY}]", style=f"dim {COLOR_PRIMARY}"))
    console.print()


def print_file_id_card(file_id: str, filename: str, size: int, expiry_days: Optional[int], auto_delete: bool) -> None:
    """Display a styled card showing the upload result and file ID."""
    size_str = _format_size(size)
    expiry_str = f"{expiry_days} day(s)" if expiry_days else "Never"
    auto_del_str = "Yes" if auto_delete else "No"

    table = Table(
        show_header=False,
        box=box.DOUBLE_EDGE,
        border_style=COLOR_SUCCESS,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Label", style=f"bold {COLOR_DIM}", width=18)
    table.add_column("Value", style=COLOR_HIGHLIGHT)

    table.add_row("File",        filename)
    table.add_row("Size",        size_str)
    table.add_row("Expires in",  expiry_str)
    table.add_row("Auto-delete", auto_del_str)
    table.add_row("", "")
    table.add_row(
        "Your File ID",
        Text(file_id, style=f"bold {COLOR_PRIMARY}"),
    )

    console.print()
    console.print(
        Panel(
            Align.center(table),
            title=f"[bold {COLOR_SUCCESS}]✓ Upload Successful[/bold {COLOR_SUCCESS}]",
            border_style=COLOR_SUCCESS,
            padding=(1, 4),
        )
    )
    console.print()
    console.print(
        f"  [{COLOR_DIM}]Share this ID with the recipient. Keep it safe![/{COLOR_DIM}]"
    )
    console.print()


def print_download_result(dest_path: Path, original_name: str, size: int, download_count: int) -> None:
    """Display a styled card showing the download result."""
    table = Table(
        show_header=False,
        box=box.DOUBLE_EDGE,
        border_style=COLOR_SUCCESS,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Label", style=f"bold {COLOR_DIM}", width=18)
    table.add_column("Value", style=COLOR_HIGHLIGHT)

    table.add_row("File",           original_name)
    table.add_row("Size",           _format_size(size))
    table.add_row("Saved to",       str(dest_path))
    table.add_row("Download #",     str(download_count))

    console.print()
    console.print(
        Panel(
            Align.center(table),
            title=f"[bold {COLOR_SUCCESS}]✓ Download Complete[/bold {COLOR_SUCCESS}]",
            border_style=COLOR_SUCCESS,
            padding=(1, 4),
        )
    )
    console.print()


def print_security_warning(reason: str) -> None:
    """Display a prominent security warning panel."""
    console.print()
    console.print(
        Panel(
            f"[bold {COLOR_ERROR}]SECURITY THREAT DETECTED[/bold {COLOR_ERROR}]\n\n"
            f"[{COLOR_WARNING}]{reason}[/{COLOR_WARNING}]\n\n"
            f"[{COLOR_DIM}]This file has been rejected and will not be uploaded.[/{COLOR_DIM}]",
            title=f"[bold {COLOR_ERROR}]⚠ UPLOAD BLOCKED[/bold {COLOR_ERROR}]",
            border_style=COLOR_ERROR,
            padding=(1, 4),
        )
    )
    console.print()


def _format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.2f} GB"
