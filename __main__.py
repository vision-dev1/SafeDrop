# Codes By Visionnn

import sys
from pathlib import Path

from rich.console import Console

from cli import (
    console,
    print_banner,
    print_main_menu,
    prompt_menu_choice,
    print_info,
    print_error,
    COLOR_DIM,
    COLOR_PRIMARY,
)
from config import STORAGE_DIR, BASE_DIR
from logger import log
from metadata import cleanup_expired
from storage import flatten_storage


def _initialize() -> None:
    """Create required directories and run startup maintenance."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Flatten any nested subdirectories inside storage (files must live at top level)
    try:
        moved = flatten_storage()
        if moved:
            log.info(f"Startup: flattened {moved} file(s) from nested storage subdirectories.")
    except Exception as e:
        log.warning(f"Startup storage flatten failed: {e}")

    # Clean up expired files silently on startup
    try:
        removed = cleanup_expired()
        if removed:
            log.info(f"Startup cleanup: removed {removed} expired file(s).")
    except Exception as e:
        log.warning(f"Startup cleanup failed: {e}")


def main() -> None:
    """Main application entry point."""
    _initialize()
    print_banner()

    while True:
        print_main_menu()

        try:
            choice = prompt_menu_choice()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n\n  [{COLOR_DIM}]Interrupted. Goodbye![/{COLOR_DIM}]\n")
            sys.exit(0)

        if choice == "1":
            from upload import run_upload
            try:
                run_upload()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n  [{COLOR_DIM}]Upload cancelled.[/{COLOR_DIM}]")
            except Exception as e:
                print_error(f"Unexpected error during upload: {e}")
                log.exception(f"Unexpected upload error: {e}")

        elif choice == "2":
            from download import run_download
            try:
                run_download()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n  [{COLOR_DIM}]Download cancelled.[/{COLOR_DIM}]")
            except Exception as e:
                print_error(f"Unexpected error during download: {e}")
                log.exception(f"Unexpected download error: {e}")

        elif choice == "3":
            console.print(f"\n  [{COLOR_DIM}]Thank you for using SafeDrop. Goodbye![/{COLOR_DIM}]\n")
            sys.exit(0)

        # Pause before returning to menu
        try:
            console.print(f"\n  [{COLOR_DIM}]Press Enter to return to the main menu...[/{COLOR_DIM}]", end="")
            input()
        except (KeyboardInterrupt, EOFError):
            console.print()


if __name__ == "__main__":
    main()

