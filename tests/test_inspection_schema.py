import json
import zipfile

import pytest

from Pagonic.core.formats.inspection import (
    ARCHIVE_ENTRY_FIELDS,
    ARCHIVE_REPORT_FIELDS,
    INSPECTION_SCHEMA_VERSION,
    ArchiveRisk,
    inspect_archive,
)
from Pagonic.core.formats.security import ZipConstants


def _mark_entries_encrypted(path):
    """Mark synthetic ZIP entries as encrypted without storing secrets."""
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


def test_entries_preserve_archive_order_and_repeat_deterministically(tmp_path):
    archive = tmp_path / "ordered.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("z-last.txt", b"last")
        zip_file.writestr("a-first.txt", b"first")
        zip_file.writestr("nested/middle.txt", b"middle")

    first = inspect_archive(archive)
    second = inspect_archive(archive)

    assert [entry.original_name for entry in first.entries] == [
        "z-last.txt",
        "a-first.txt",
        "nested/middle.txt",
    ]
    assert first.to_dict() == second.to_dict()
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(), sort_keys=True
    )


def test_schema_v1_has_canonical_fields_then_compatibility_aliases(tmp_path):
    archive = tmp_path / "schema.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("docs/readme.txt", b"hello")

    payload = inspect_archive(archive).to_dict()
    entry = payload["entries"][0]

    assert payload["schema_version"] == INSPECTION_SCHEMA_VERSION == "1"
    assert tuple(payload) == ARCHIVE_REPORT_FIELDS
    assert tuple(entry) == ARCHIVE_ENTRY_FIELDS
    assert payload["compression_ratio"] == payload["global_compression_ratio"]
    assert entry["filename"] == entry["original_name"]
    assert entry["safe_path"] == entry["safe_name"]


def test_risk_flags_are_catalog_ordered_independent_of_entry_order(tmp_path):
    archive = tmp_path / "risk-order.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(r"C:\Users\Admin\file.doc", b"drive")
        zip_file.writestr("/etc/passwd", b"posix")

    report = inspect_archive(archive)

    assert report.risk_flags == [
        ArchiveRisk.ABSOLUTE_PATH,
        ArchiveRisk.WINDOWS_DRIVE_PATH,
    ]
    assert report.entries[0].risk_flags == [ArchiveRisk.WINDOWS_DRIVE_PATH]
    assert report.entries[1].risk_flags == [ArchiveRisk.ABSOLUTE_PATH]


def test_warnings_follow_documented_category_and_entry_order(tmp_path, monkeypatch):
    pytest.importorskip("bz2")
    archive = tmp_path / "diagnostics.zip"
    monkeypatch.setattr(ZipConstants, "MAX_FILES_IN_ZIP", 1)
    monkeypatch.setattr(ZipConstants, "MAX_UNCOMPRESSED_SIZE", 1)

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_BZIP2) as zip_file:
        zip_file.comment = b"c" * (ZipConstants.MAX_ARCHIVE_COMMENT_LENGTH + 1)
        zip_file.writestr("z-encrypted.txt", b"a")
        zip_file.writestr("a-unsupported.txt", b"b")
    _mark_entries_encrypted(archive)

    report = inspect_archive(archive)

    assert report.warnings == [
        "Archive contains too many files: 2",
        "Archive comment exceeds the configured review limit: "
        f"{ZipConstants.MAX_ARCHIVE_COMMENT_LENGTH + 1} bytes",
        "CRC validation skipped for encrypted entries: "
        "z-encrypted.txt, a-unsupported.txt",
        "CRC validation skipped for unsupported compression methods: "
        "z-encrypted.txt, a-unsupported.txt",
        "Archive exceeds uncompressed size limit: 2",
    ]
    assert report.errors == []


def test_invalid_archive_errors_are_stable_and_separate_from_findings(tmp_path):
    archive = tmp_path / "invalid.zip"
    archive.write_bytes(b"not a ZIP archive")

    first = inspect_archive(archive)
    second = inspect_archive(archive)

    assert first.errors == second.errors
    assert len(first.errors) == 1
    assert first.risk_flags == [ArchiveRisk.CRC_OR_STRUCTURE_ERROR]
    assert first.entries == []
