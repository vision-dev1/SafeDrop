# Codes By Visionnn

import secrets
import string
from config import ID_LENGTH


# Character set: uppercase letters + digits (no ambiguous chars like 0/O, 1/I/l)
_ALPHABET = string.ascii_uppercase + string.digits
_ALPHABET = _ALPHABET.replace("O", "").replace("I", "").replace("0", "").replace("1", "")


def generate_id() -> str:
    """
    Generate a cryptographically secure unique file ID.

    Returns a 12-character alphanumeric string using the `secrets` module,
    which is suitable for security-sensitive applications.

    Format: XXXX-XXXX-XXXX (groups of 4 separated by dashes for readability)
    """
    group_size = ID_LENGTH // 3
    groups = [
        "".join(secrets.choice(_ALPHABET) for _ in range(group_size))
        for _ in range(3)
    ]
    return "-".join(groups)


def strip_dashes(file_id: str) -> str:
    """Remove dashes from a file ID for internal storage key use."""
    return file_id.replace("-", "").upper()


def normalize_id(file_id: str) -> str:
    """
    Normalize a user-provided ID:
    - Strip whitespace
    - Uppercase
    - Re-insert dashes if missing
    """
    raw = file_id.strip().upper().replace("-", "").replace(" ", "")
    if len(raw) == ID_LENGTH:
        group_size = ID_LENGTH // 3
        return f"{raw[:group_size]}-{raw[group_size:group_size*2]}-{raw[group_size*2:]}"
    return file_id.strip().upper()


def is_valid_id_format(file_id: str) -> bool:
    """
    Validate that a file ID matches the expected format.
    Accepts both dashed (XXXX-XXXX-XXXX) and plain (XXXXXXXXXXXX) formats.
    """
    normalized = file_id.strip().upper().replace("-", "")
    if len(normalized) != ID_LENGTH:
        return False
    valid_chars = set(_ALPHABET)
    return all(c in valid_chars for c in normalized)

