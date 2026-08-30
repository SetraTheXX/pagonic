"""Small, generated ZIP inputs for security regression tests."""

import io
from pathlib import Path
import stat
import unicodedata
import warnings
import zipfile

from Pagonic.core.formats.security import ZipConstants


def _write_entries(
    path: Path,
    entries: list[tuple[str | zipfile.ZipInfo, bytes]],
    *,
    compression: int = zipfile.ZIP_DEFLATED,
) -> Path:
    """Write deterministic synthetic entries without storing ZIP fixtures."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", compression) as archive:
            for name, data in entries:
                archive.writestr(name, data)
    return path


def build_traversal_fixture(path: Path) -> Path:
    """Create a ZIP entry using both supported path separator styles."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(r"..\../safe/evil.txt", b"synthetic traversal fixture")
    return path


def build_duplicate_fixture(path: Path) -> Path:
    """Create two entries with the same archive name."""
    return _write_entries(
        path,
        [
            ("duplicate.txt", b"first"),
            ("duplicate.txt", b"second"),
        ],
    )


def build_normalized_collision_fixture(path: Path) -> Path:
    """Create distinct names that map to the same sanitized path."""
    return _write_entries(
        path,
        [
            ("./same.txt", b"dot segment"),
            ("same.txt", b"canonical"),
        ],
    )


def build_case_collision_fixture(path: Path) -> Path:
    """Create names that differ only by letter case."""
    return _write_entries(
        path,
        [
            ("Readme.txt", b"upper case"),
            ("readme.txt", b"lower case"),
        ],
    )


def build_unicode_collision_fixture(path: Path) -> Path:
    """Create canonically equivalent NFC and NFD names."""
    composed = unicodedata.normalize("NFC", "café.txt")
    decomposed = unicodedata.normalize("NFD", "café.txt")
    return _write_entries(
        path,
        [
            (composed, b"composed"),
            (decomposed, b"decomposed"),
        ],
    )


def build_absolute_path_fixture(path: Path) -> Path:
    """Create POSIX and Windows absolute-looking member names."""
    return _write_entries(
        path,
        [
            ("/etc/passwd", b"synthetic absolute path"),
            (r"C:\Users\Admin\file.doc", b"synthetic drive path"),
        ],
    )


def build_symlink_fixture(path: Path) -> Path:
    """Create symlink metadata without creating a filesystem symlink."""
    symlink_info = zipfile.ZipInfo("link")
    symlink_info.create_system = 3
    symlink_info.external_attr = (stat.S_IFLNK | 0o777) << 16
    return _write_entries(path, [(symlink_info, b"target.txt")])


def _mark_zip_entries_encrypted(path: Path) -> Path:
    """Set the encryption bit on metadata without encrypting test content."""
    data = bytearray(path.read_bytes())
    for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        position = 0
        while True:
            position = data.find(signature, position)
            if position < 0:
                break
            flags = int.from_bytes(
                data[position + flag_offset:position + flag_offset + 2],
                "little",
            )
            data[position + flag_offset:position + flag_offset + 2] = (
                flags | 0x1
            ).to_bytes(2, "little")
            position += len(signature)
    path.write_bytes(data)
    return path


def build_encrypted_fixture(path: Path) -> Path:
    """Create a metadata-only encrypted-entry marker for inspection tests."""
    _write_entries(path, [("secret.txt", b"synthetic encrypted marker")])
    return _mark_zip_entries_encrypted(path)


def build_unsupported_method_fixture(path: Path) -> Path:
    """Create a valid BZIP2 entry, unsupported by Pagonic extraction."""
    return _write_entries(
        path,
        [("data.txt", b"synthetic unsupported method")],
        compression=zipfile.ZIP_BZIP2,
    )


def build_nested_archive_fixture(path: Path) -> Path:
    """Create a small ZIP containing another ZIP as an opaque member."""
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("inner.txt", b"synthetic nested payload")
    return _write_entries(path, [("payload.zip", inner.getvalue())])


def build_long_metadata_fixture(path: Path) -> Path:
    """Create metadata just beyond the configured review thresholds."""
    long_name = "a" * (ZipConstants.MAX_PATH_LENGTH + 1) + ".txt"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.comment = b"c" * (ZipConstants.MAX_ARCHIVE_COMMENT_LENGTH + 1)
        archive.writestr(long_name, b"synthetic long metadata")
    return path


def build_corrupt_structure_fixture(path: Path) -> Path:
    """Corrupt a ZIP end marker after creating a valid small archive."""
    _write_entries(path, [("valid.txt", b"synthetic structure fixture")])
    data = bytearray(path.read_bytes())
    end_record = data.rfind(b"PK\x05\x06")
    if end_record < 0:
        raise AssertionError("Synthetic ZIP did not contain an end record")
    data[end_record:end_record + 4] = b"BAD!"
    path.write_bytes(data)
    return path


def build_clean_fixture(path: Path) -> Path:
    """Create the no-risk control archive used by extraction assertions."""
    return _write_entries(path, [("docs/readme.txt", b"synthetic clean payload")])


def build_too_many_files_fixture(path: Path) -> Path:
    """Create a small archive whose entry count can exceed a patched limit."""
    return _write_entries(
        path,
        [
            ("one.txt", b"1"),
            ("two.txt", b"2"),
            ("three.txt", b"3"),
        ],
    )


def build_large_uncompressed_fixture(path: Path) -> Path:
    """Create a small payload whose size can exceed a patched limit."""
    return _write_entries(path, [("large.txt", b"0123456789abcdef")])


def build_high_ratio_fixture(path: Path) -> Path:
    """Create a small repetitive payload for a patched ratio limit."""
    return _write_entries(path, [("repetitive.txt", b"A" * 4096)])
