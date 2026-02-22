"""
Tests for storage.flatten_storage()
Verifies that nested subdirectories are detected, their files moved to STORAGE_DIR,
and the empty subdirectories removed.
"""

import shutil
from pathlib import Path

import pytest

from storage import flatten_storage


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect STORAGE_DIR to a temp directory for each test."""
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setattr("storage.STORAGE_DIR", storage)
    yield storage


class TestFlattenStorage:
    def test_no_subdirs_is_noop(self, isolated_storage):
        """When there are no subdirectories, flatten_storage returns 0."""
        (isolated_storage / "ABCDWXYZ2345.sdf").write_bytes(b"file1")
        result = flatten_storage()
        assert result == 0
        assert (isolated_storage / "ABCDWXYZ2345.sdf").exists()

    def test_moves_files_from_nested_dir(self, isolated_storage):
        """Files inside a nested subdirectory are moved to STORAGE_DIR."""
        nested = isolated_storage / "inner"
        nested.mkdir()
        (nested / "ABCDWXYZ2345.sdf").write_bytes(b"secret")

        result = flatten_storage()

        assert result == 1
        assert (isolated_storage / "ABCDWXYZ2345.sdf").exists()
        assert (isolated_storage / "ABCDWXYZ2345.sdf").read_bytes() == b"secret"
        assert not nested.exists()

    def test_removes_empty_nested_dir(self, isolated_storage):
        """The nested subdirectory itself is deleted after files are moved."""
        nested = isolated_storage / "subdir"
        nested.mkdir()
        (nested / "file.sdf").write_bytes(b"data")

        flatten_storage()

        assert not nested.exists()

    def test_handles_deeply_nested_files(self, isolated_storage):
        """Files nested multiple levels deep are all moved to STORAGE_DIR."""
        deep = isolated_storage / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.sdf").write_bytes(b"deep content")

        result = flatten_storage()

        assert result == 1
        assert (isolated_storage / "deep.sdf").exists()
        assert not (isolated_storage / "a").exists()

    def test_collision_renamed_with_suffix(self, isolated_storage):
        """If a filename already exists in STORAGE_DIR, the moved file is renamed."""
        # Pre-existing file at top level
        (isolated_storage / "clash.sdf").write_bytes(b"original")

        # Same filename inside a nested dir
        nested = isolated_storage / "sub"
        nested.mkdir()
        (nested / "clash.sdf").write_bytes(b"incoming")

        result = flatten_storage()

        assert result == 1
        # Original untouched
        assert (isolated_storage / "clash.sdf").read_bytes() == b"original"
        # Incoming renamed
        assert (isolated_storage / "clash_1.sdf").exists()
        assert (isolated_storage / "clash_1.sdf").read_bytes() == b"incoming"

    def test_multiple_nested_dirs(self, isolated_storage):
        """Multiple nested directories are all flattened in one call."""
        for name in ("dir1", "dir2", "dir3"):
            d = isolated_storage / name
            d.mkdir()
            (d / f"{name}.sdf").write_bytes(name.encode())

        result = flatten_storage()

        assert result == 3
        for name in ("dir1", "dir2", "dir3"):
            assert (isolated_storage / f"{name}.sdf").exists()
            assert not (isolated_storage / name).exists()

    def test_non_sdf_files_also_moved(self, isolated_storage):
        """Any file type inside a nested dir is moved, not just .sdf."""
        nested = isolated_storage / "misc"
        nested.mkdir()
        (nested / "readme.txt").write_bytes(b"notes")

        result = flatten_storage()

        assert result == 1
        assert (isolated_storage / "readme.txt").exists()
