"""
Tests for id_generator
"""

import pytest
from id_generator import generate_id, normalize_id, is_valid_id_format, strip_dashes


class TestGenerateId:
    def test_format(self):
        """ID should be in XXXX-XXXX-XXXX format."""
        file_id = generate_id()
        parts = file_id.split("-")
        assert len(parts) == 3
        assert all(len(p) == 4 for p in parts)

    def test_uppercase(self):
        """ID should be uppercase."""
        file_id = generate_id()
        assert file_id == file_id.upper()

    def test_no_ambiguous_chars(self):
        """ID should not contain O, I, 0, or 1."""
        for _ in range(200):
            file_id = generate_id()
            raw = file_id.replace("-", "")
            for bad_char in ("O", "I", "0", "1"):
                assert bad_char not in raw, f"Ambiguous char '{bad_char}' found in ID: {file_id}"

    def test_uniqueness(self):
        """Generate 10,000 IDs and verify no collisions."""
        ids = {generate_id() for _ in range(10_000)}
        assert len(ids) == 10_000

    def test_length(self):
        """Raw ID (no dashes) should be 12 characters."""
        file_id = generate_id()
        assert len(file_id.replace("-", "")) == 12


class TestNormalizeId:
    def test_adds_dashes(self):
        """Plain 12-char ID should get dashes inserted."""
        result = normalize_id("ABCDWXYZ2345")
        assert result == "ABCD-WXYZ-2345"

    def test_handles_existing_dashes(self):
        """Already-dashed ID should be returned normalized."""
        result = normalize_id("abcd-wxyz-2345")
        assert result == "ABCD-WXYZ-2345"

    def test_strips_whitespace(self):
        result = normalize_id("  ABCD-WXYZ-2345  ")
        assert result == "ABCD-WXYZ-2345"


class TestIsValidIdFormat:
    def test_valid_dashed(self):
        assert is_valid_id_format("ABCD-WXYZ-2345") is True

    def test_valid_plain(self):
        assert is_valid_id_format("ABCDWXYZ2345") is True

    def test_too_short(self):
        assert is_valid_id_format("ABCD-WXYZ") is False

    def test_invalid_chars(self):
        assert is_valid_id_format("ABCD-WXYZ-!!!") is False

    def test_empty(self):
        assert is_valid_id_format("") is False
