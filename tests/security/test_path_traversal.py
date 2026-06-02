"""
Security Tests - Path Traversal Prevention
==========================================
Tests for sanitize_path() function to prevent path traversal attacks.

"""

import pytest
from pathlib import Path
from Pagonic.core.formats.security import sanitize_path, is_safe_filename
from Pagonic.core.formats.errors import ValidationError


class TestPathTraversalPrevention:
    """Test suite for path traversal attack prevention."""

    def test_path_traversal_attacks(self):
        """Test that path traversal patterns are blocked."""
        malicious_paths = [
            "../../etc/passwd",
            "../../../etc/shadow",
            "..\\..\\windows\\system32",
            "folder/../../../etc/passwd",
            "test/../../secret.txt",
        ]

        for path in malicious_paths:
            safe = sanitize_path(path)
            # After sanitization, should have no path separators or '..'
            assert ".." not in safe, f"Path traversal not removed from: {path}"
            assert "/" not in safe, f"Forward slash not removed from: {path}"
            assert "\\" not in safe, f"Backslash not removed from: {path}"

    def test_hidden_file_rejection(self):
        """Test that hidden files (basename starting with .) are rejected."""
        # These have basenames that start with "." after extraction
        hidden_files = [
            ".hidden_file",  # Basename: .hidden_file
            ".env",          # Basename: .env
        ]

        for hidden in hidden_files:
            with pytest.raises(ValidationError, match="Hidden files not allowed"):
                sanitize_path(hidden)

    def test_hidden_directory_extraction(self):
        """Test that files in hidden directories are extracted correctly."""
        # These are in hidden directories but basenames don't start with "."
        paths_in_hidden_dirs = [
            ".ssh/id_rsa",      # Basename: id_rsa (safe)
            ".git/config",      # Basename: config (safe)
            ".cache/data.txt",  # Basename: data.txt (safe)
        ]

        expected_basenames = [
            "id_rsa",
            "config",
            "data.txt",
        ]

        for path, expected in zip(paths_in_hidden_dirs, expected_basenames):
            result = sanitize_path(path)
            assert result == expected
            assert not result.startswith('.')  # Basename should not start with .

    def test_empty_filename_rejection(self):
        """Test that empty filenames are rejected."""
        with pytest.raises(ValidationError, match="Invalid or empty filename"):
            sanitize_path("")

    def test_filename_length_limit(self):
        """Test that overly long filenames are rejected."""
        long_filename = "a" * 300  # Exceeds 256 char limit

        with pytest.raises(ValidationError, match="Filename too long"):
            sanitize_path(long_filename)

    def test_null_byte_removal(self):
        """Test that null bytes are removed from filenames."""
        malicious = "file\x00.txt"
        safe = sanitize_path(malicious)
        assert "\x00" not in safe

    def test_safe_filename_accepted(self):
        """Test that normal, safe filenames are accepted."""
        safe_files = [
            "document.txt",
            "report.pdf",
            "archive.zip",
            "photo_2024.jpg",
        ]

        for filename in safe_files:
            result = sanitize_path(filename)
            assert result == filename
            assert is_safe_filename(result)

    def test_basename_only(self):
        """Test that only basename is kept, directory is removed."""
        paths = [
            "/home/user/document.txt",
            "C:\\Users\\Admin\\file.doc",
            "folder/subfolder/file.zip",
        ]

        expected = [
            "document.txt",
            "file.doc",
            "file.zip",
        ]

        for path, expected_result in zip(paths, expected):
            result = sanitize_path(path)
            assert result == expected_result

    def test_is_safe_filename_function(self):
        """Test is_safe_filename() utility function."""
        # Safe filenames
        assert is_safe_filename("document.txt")
        assert is_safe_filename("file_2024.zip")

        # Unsafe filenames
        assert not is_safe_filename("../etc/passwd")
        assert not is_safe_filename(".hidden")
        assert not is_safe_filename("file/with/slashes.txt")
        assert not is_safe_filename("a" * 300)  # Too long


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
