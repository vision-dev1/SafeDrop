# Codes By Visionnn

import logging
import sys
from pathlib import Path
from config import LOG_FILE, APP_NAME


def get_logger(name: str = APP_NAME) -> logging.Logger:
    """
    Returns a configured logger that writes to both file and stderr (errors only).
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)

    # ── File Handler (all levels) ──────────────────────────────────────────────
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # ── Stderr Handler (WARNING and above only) ────────────────────────────────
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_fmt = logging.Formatter(fmt="[%(levelname)s] %(message)s")
    stderr_handler.setFormatter(stderr_fmt)
    logger.addHandler(stderr_handler)

    return logger


# Module-level logger instance
log = get_logger()

