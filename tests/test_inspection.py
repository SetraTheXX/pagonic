import json
import stat
import unicodedata
import warnings
import zipfile

import pytest

from Pagonic.core.formats.inspection import (
    ARCHIVE_ENTRY_FIELDS,
    ARCHIVE_REPORT_FIELDS,
    INSPECTION_SCHEMA_VERSION,
    ArchiveRisk,
    RISK_CATALOG,
    get_risk_definition,
    inspect_archive,
)
from Pagonic.core.formats.security import ZipConstants
from Pagonic.core.formats.zip_reader import ZipReader


def _make_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def _mark_zip_entries_encrypted(path):
    """Set the ZIP encryption flag without pretending to encrypt test content."""
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


def test_risk_catalog_defines_stable_metadata_for_all_flags():
    expected_flags = {
        ArchiveRisk.PATH_TRAVERSAL,
        ArchiveRisk.ABSOLUTE_PATH,
        ArchiveRisk.WINDOWS_DRIVE_PATH,
        ArchiveRisk.HIDDEN_FILE,
        ArchiveRisk.EMPTY_FILENAME,
        ArchiveRisk.TOO_MANY_FILES,
        ArchiveRisk.LARGE_UNCOMPRESSED_SIZE,
        ArchiveRisk.HIGH_COMPRESSION_RATIO,
        ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD,
        ArchiveRisk.CRC_OR_STRUCTURE_ERROR,
        ArchiveRisk.SUSPICIOUS_EXTENSION,
        ArchiveRisk.DUPLICATE_FILENAME,
        ArchiveRisk.NORMALIZED_PATH_COLLISION,
        ArchiveRisk.CASE_INSENSITIVE_COLLISION,
        ArchiveRisk.UNICODE_NORMALIZATION_COLLISION,
        ArchiveRisk.SYMLINK_ENTRY,
        ArchiveRisk.ENCRYPTED_ENTRY,
        ArchiveRisk.NESTED_ARCHIVE,
        ArchiveRisk.LONG_FILENAME,
        ArchiveRisk.LONG_ARCHIVE_COMMENT,
    }
    severities = {"ok", "low", "medium", "high", "critical"}

    assert set(RISK_CATALOG) == expected_flags
    for risk_id, definition in RISK_CATALOG.items():
        assert definition.id == risk_id
        assert definition.title
        assert definition.severity in severities
        assert definition.explanation
        assert definition.recommended_action


def test_inspect_clean_archive_reports_ok(tmp_path):
    archive = tmp_path / "clean.zip"
    _make_zip(archive, {"docs/readme.txt": b"hello", "nested/file.txt": b"world"})

    report = inspect_archive(archive)

    assert report.risk_level == "ok"
    assert report.file_count == 2
    assert report.errors == []
    assert report.risk_flags == []
    assert report.recommended_action
    assert [entry.safe_path for entry in report.entries] == ["docs/readme.txt", "nested/file.txt"]

    payload = report.to_dict()
    json.dumps(payload)
    assert tuple(payload) == ARCHIVE_REPORT_FIELDS
    assert payload["schema_version"] == INSPECTION_SCHEMA_VERSION
    assert report.schema_version == INSPECTION_SCHEMA_VERSION
    assert isinstance(payload["file_count"], int)
    assert isinstance(payload["total_compressed_size"], int)
    assert isinstance(payload["total_uncompressed_size"], int)
    assert isinstance(payload["global_compression_ratio"], float)
    assert isinstance(payload["risk_flags"], list)
    assert payload["compression_ratio"] == payload["global_compression_ratio"] == report.compression_ratio

    entry_payload = payload["entries"][0]
    assert tuple(entry_payload) == ARCHIVE_ENTRY_FIELDS
    assert isinstance(entry_payload["compressed_size"], int)
    assert isinstance(entry_payload["uncompressed_size"], int)
    assert isinstance(entry_payload["compression_method"], int)
    assert isinstance(entry_payload["compression_ratio"], float)
    assert isinstance(entry_payload["crc32"], str)
    assert isinstance(entry_payload["risk_flags"], list)
    assert entry_payload["filename"] == entry_payload["original_name"] == report.entries[0].filename
    assert entry_payload["safe_path"] == entry_payload["safe_name"] == report.entries[0].safe_path
    assert entry_payload["normalized_name"] == entry_payload["safe_name"] == report.entries[0].normalized_name


def test_risk_definition_lookup_is_explicit():
    definition = get_risk_definition(ArchiveRisk.PATH_TRAVERSAL)

    assert definition.id == ArchiveRisk.PATH_TRAVERSAL
    assert definition.to_dict()["recommended_action"] == definition.recommended_action

    with pytest.raises(KeyError):
        get_risk_definition("unknown_risk")


def test_inspect_reports_path_traversal(tmp_path):
    archive = tmp_path / "traversal.zip"
    _make_zip(archive, {"../../evil.txt": b"nope"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.PATH_TRAVERSAL in report.risk_flags
    assert report.entries[0].safe_path == "evil.txt"
    assert ArchiveRisk.PATH_TRAVERSAL in report.entries[0].risk_flags


def test_inspect_reports_mixed_separator_traversal(tmp_path):
    archive = tmp_path / "mixed.zip"
    _make_zip(archive, {r"..\../safe/evil.txt": b"nope"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.PATH_TRAVERSAL in report.risk_flags
    assert report.entries[0].safe_path == "safe/evil.txt"
    assert ArchiveRisk.PATH_TRAVERSAL in report.entries[0].risk_flags


def test_inspect_reports_windows_absolute_path(tmp_path):
    archive = tmp_path / "windows-absolute.zip"
    _make_zip(archive, {r"C:\Users\Admin\file.doc": b"data"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.WINDOWS_DRIVE_PATH in report.risk_flags
    assert report.entries[0].safe_path == "Users/Admin/file.doc"
    assert ArchiveRisk.WINDOWS_DRIVE_PATH in report.entries[0].risk_flags


def test_inspect_reports_posix_absolute_path(tmp_path):
    archive = tmp_path / "posix-absolute.zip"
    _make_zip(archive, {"/etc/passwd": b"root"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.ABSOLUTE_PATH in report.risk_flags
    assert report.entries[0].safe_path == "etc/passwd"
    assert ArchiveRisk.ABSOLUTE_PATH in report.entries[0].risk_flags


def test_inspect_reports_hidden_filename(tmp_path):
    archive = tmp_path / "hidden.zip"
    _make_zip(archive, {".env": b"SECRET=value"})

    report = inspect_archive(archive)

    assert report.risk_level == "low"
    assert ArchiveRisk.HIDDEN_FILE in report.risk_flags
    assert ArchiveRisk.HIDDEN_FILE in report.entries[0].risk_flags


def test_inspect_reports_suspicious_extension(tmp_path):
    archive = tmp_path / "suspicious.zip"
    _make_zip(archive, {"payload.exe": b"MZ"})

    report = inspect_archive(archive)

    assert report.risk_level == "medium"
    assert ArchiveRisk.SUSPICIOUS_EXTENSION in report.risk_flags
    assert ArchiveRisk.SUSPICIOUS_EXTENSION in report.entries[0].risk_flags


def test_inspect_reports_high_compression_ratio(tmp_path, monkeypatch):
    archive = tmp_path / "high-ratio.zip"
    monkeypatch.setattr(ZipConstants, "MAX_COMPRESSION_RATIO", 2)
    _make_zip(archive, {"huge.txt": b"A" * 4096})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.HIGH_COMPRESSION_RATIO in report.risk_flags
    assert ArchiveRisk.HIGH_COMPRESSION_RATIO in report.entries[0].risk_flags


def test_inspect_reports_too_many_files(tmp_path, monkeypatch):
    archive = tmp_path / "many-files.zip"
    monkeypatch.setattr(ZipConstants, "MAX_FILES_IN_ZIP", 1)
    _make_zip(archive, {"one.txt": b"1", "two.txt": b"2"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.TOO_MANY_FILES in report.risk_flags
    assert report.warnings


def test_inspect_reports_unsupported_compression_method(tmp_path):
    archive = tmp_path / "unsupported.zip"
    try:
        import bz2  # noqa: F401
    except ImportError:
        pytest.skip("Python bz2 support is unavailable")

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_BZIP2) as zip_file:
        zip_file.writestr("data.txt", b"content")

    report = inspect_archive(archive)

    assert report.risk_level == "medium"
    assert ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD in report.risk_flags
    assert ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD in report.entries[0].risk_flags


def test_inspect_reports_duplicate_and_normalized_path_collisions(tmp_path):
    archive = tmp_path / "collisions.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("duplicate.txt", b"first")
            zip_file.writestr("duplicate.txt", b"second")
            zip_file.writestr("./same.txt", b"normalized")
            zip_file.writestr("same.txt", b"target")

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.DUPLICATE_FILENAME in report.risk_flags
    assert ArchiveRisk.NORMALIZED_PATH_COLLISION in report.risk_flags
    assert all(
        ArchiveRisk.DUPLICATE_FILENAME in entry.risk_flags
        for entry in report.entries[:2]
    )
    assert all(
        ArchiveRisk.NORMALIZED_PATH_COLLISION in entry.risk_flags
        for entry in report.entries[2:]
    )


def test_inspect_reports_case_insensitive_collision(tmp_path):
    archive = tmp_path / "case-collision.zip"
    _make_zip(archive, {"Readme.txt": b"one", "readme.txt": b"two"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.CASE_INSENSITIVE_COLLISION in report.risk_flags
    assert all(
        ArchiveRisk.CASE_INSENSITIVE_COLLISION in entry.risk_flags
        for entry in report.entries
    )


def test_inspect_reports_unicode_normalization_collision(tmp_path):
    archive = tmp_path / "unicode-collision.zip"
    composed = unicodedata.normalize("NFC", "café.txt")
    decomposed = unicodedata.normalize("NFD", "café.txt")
    _make_zip(archive, {composed: b"one", decomposed: b"two"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.UNICODE_NORMALIZATION_COLLISION in report.risk_flags
    assert all(
        ArchiveRisk.UNICODE_NORMALIZATION_COLLISION in entry.risk_flags
        for entry in report.entries
    )


def test_inspect_reports_symlink_metadata(tmp_path):
    archive = tmp_path / "symlink.zip"
    symlink_info = zipfile.ZipInfo("link")
    symlink_info.create_system = 3
    symlink_info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr(symlink_info, b"target.txt")

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.SYMLINK_ENTRY in report.risk_flags
    assert ArchiveRisk.SYMLINK_ENTRY in report.entries[0].risk_flags


def test_inspect_reports_encrypted_entry_without_crashing(tmp_path):
    archive = tmp_path / "encrypted.zip"
    _make_zip(archive, {"secret.txt": b"secret"})
    _mark_zip_entries_encrypted(archive)

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert ArchiveRisk.ENCRYPTED_ENTRY in report.risk_flags
    assert ArchiveRisk.ENCRYPTED_ENTRY in report.entries[0].risk_flags
    assert report.errors == []
    assert report.warnings


def test_inspect_reports_nested_archive(tmp_path):
    archive = tmp_path / "nested.zip"
    _make_zip(archive, {"payload.zip": b"not recursively inspected"})

    report = inspect_archive(archive)

    assert report.risk_level == "low"
    assert ArchiveRisk.NESTED_ARCHIVE in report.risk_flags
    assert ArchiveRisk.NESTED_ARCHIVE in report.entries[0].risk_flags


def test_inspect_reports_long_filename_and_comment(tmp_path):
    archive = tmp_path / "long-metadata.zip"
    long_name = "a" * (ZipConstants.MAX_PATH_LENGTH + 1) + ".txt"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.comment = b"c" * (ZipConstants.MAX_ARCHIVE_COMMENT_LENGTH + 1)
        zip_file.writestr(long_name, b"long name")

    report = inspect_archive(archive)

    assert report.risk_level == "medium"
    assert ArchiveRisk.LONG_FILENAME in report.risk_flags
    assert ArchiveRisk.LONG_FILENAME in report.entries[0].risk_flags
    assert ArchiveRisk.LONG_ARCHIVE_COMMENT in report.risk_flags
    assert report.warnings


def test_risk_flags_are_deterministic_catalog_order(tmp_path, monkeypatch):
    archive = tmp_path / "ordered-risks.zip"
    monkeypatch.setattr(ZipConstants, "MAX_COMPRESSION_RATIO", 2)
    try:
        import bz2  # noqa: F401
    except ImportError:
        pytest.skip("Python bz2 support is unavailable")

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_BZIP2) as zip_file:
        zip_file.writestr("../payload.exe", b"A" * 4096)

    report = inspect_archive(archive)

    assert report.entries[0].risk_flags == [
        ArchiveRisk.PATH_TRAVERSAL,
        ArchiveRisk.HIGH_COMPRESSION_RATIO,
        ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD,
        ArchiveRisk.SUSPICIOUS_EXTENSION,
    ]
    assert report.risk_flags == report.entries[0].risk_flags


def test_inspect_corrupt_archive_returns_critical_report(tmp_path):
    archive = tmp_path / "broken.zip"
    archive.write_bytes(b"not a real zip")

    report = inspect_archive(archive)

    assert report.risk_level == "critical"
    assert report.file_count == 0
    assert ArchiveRisk.CRC_OR_STRUCTURE_ERROR in report.risk_flags
    assert report.recommended_action
    assert report.errors


def test_zip_reader_inspect_delegates_to_inspection_service(tmp_path):
    archive = tmp_path / "reader.zip"
    _make_zip(archive, {"file.txt": b"hello"})

    direct_report = inspect_archive(archive)
    reader_report = ZipReader(str(archive)).inspect()

    assert reader_report.to_dict() == direct_report.to_dict()
    assert reader_report.risk_level == "ok"
    assert reader_report.entries[0].filename == "file.txt"


def test_zip_reader_exposes_entry_metadata_through_public_api(tmp_path):
    archive = tmp_path / "entries.zip"
    _make_zip(archive, {"folder/file.txt": b"hello"})

    reader = ZipReader(str(archive))
    entries = reader.get_entries()

    assert len(entries) == 1
    assert entries[0].filename == "folder/file.txt"
    assert reader.get_entries() is not entries
