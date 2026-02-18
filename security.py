"""
SafeDrop Security Scanner
Scans files for malicious content before allowing upload.

Checks performed:
  1. File extension against dangerous types
  2. Magic bytes / file signatures
  3. Shannon entropy (detects packed/encrypted malware)
  4. Suspicious script patterns
"""

import math
import os
from pathlib import Path
from typing import Tuple

from config import (
    DANGEROUS_EXTENSIONS,
    DANGEROUS_SIGNATURES,
    SUSPICIOUS_PATTERNS,
    ENTROPY_THRESHOLD,
    ENTROPY_SAMPLE_SIZE,
)
from logger import log


ScanResult = Tuple[bool, str]  # (is_safe, reason)


def check_extension(filepath: Path) -> ScanResult:
    """Check if the file extension is in the dangerous list."""
    ext = filepath.suffix.lower()
    if ext in DANGEROUS_EXTENSIONS:
        return False, f"Dangerous file extension detected: '{ext}'"
    return True, ""


def check_magic_bytes(filepath: Path) -> ScanResult:
    """
    Read the first bytes of the file and compare against known
    executable/malicious file signatures.
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
    except OSError as e:
        log.warning(f"Could not read file for magic byte check: {e}")
        return True, ""  # Can't read → don't block, but log

    for offset, signature, description in DANGEROUS_SIGNATURES:
        chunk = header[offset: offset + len(signature)]
        if chunk == signature:
            return False, f"Dangerous file signature detected: {description}"

    return True, ""


def _calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of a byte sequence."""
    if not data:
        return 0.0
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    length = len(data)
    entropy = 0.0
    for count in freq:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return entropy


def check_entropy(filepath: Path) -> ScanResult:
    """
    Calculate Shannon entropy on a sample of the file.
    High entropy (> threshold) may indicate packed/encrypted malware.
    """
    try:
        with open(filepath, "rb") as f:
            sample = f.read(ENTROPY_SAMPLE_SIZE)
    except OSError as e:
        log.warning(f"Could not read file for entropy check: {e}")
        return True, ""

    # Skip very small files (< 512 bytes) — entropy is unreliable
    if len(sample) < 512:
        return True, ""

    entropy = _calculate_entropy(sample)
    if entropy > ENTROPY_THRESHOLD:
        return (
            False,
            f"Suspiciously high entropy ({entropy:.2f}/8.0) — file may be packed, "
            f"encrypted, or obfuscated malware.",
        )
    return True, ""


def check_script_patterns(filepath: Path) -> ScanResult:
    """
    Scan text-like files for known malicious script patterns.
    Only applied to files under 10 MB to avoid performance issues.
    """
    max_scan_size = 10 * 1024 * 1024  # 10 MB
    try:
        size = filepath.stat().st_size
        if size > max_scan_size:
            return True, ""  # Too large to pattern-scan efficiently

        with open(filepath, "rb") as f:
            content = f.read()
    except OSError as e:
        log.warning(f"Could not read file for pattern check: {e}")
        return True, ""

    content_upper = content.upper()
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.upper() in content_upper:
            return (
                False,
                f"Suspicious script pattern detected: '{pattern.decode('utf-8', errors='replace')}'",
            )

    return True, ""


def scan_file(filepath: Path) -> ScanResult:
    """
    Run all security checks on a file.

    Returns:
        (True, "") if the file passes all checks.
        (False, reason) if any check fails, with a human-readable reason.
    """
    filepath = Path(filepath)

    log.info(f"Scanning file: {filepath.name}")

    checks = [
        ("Extension check",       check_extension),
        ("Magic bytes check",     check_magic_bytes),
        ("Entropy check",         check_entropy),
        ("Script pattern check",  check_script_patterns),
    ]

    for check_name, check_fn in checks:
        is_safe, reason = check_fn(filepath)
        if not is_safe:
            log.warning(f"Security check FAILED [{check_name}] for '{filepath.name}': {reason}")
            return False, reason
        log.debug(f"  ✓ {check_name} passed")

    log.info(f"File '{filepath.name}' passed all security checks.")
    return True, ""
