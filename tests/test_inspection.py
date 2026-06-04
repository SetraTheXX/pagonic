import json
import zipfile

import pytest

from Pagonic.core.formats.inspection import ArchiveRisk, RISK_CATALOG, inspect_archive
from Pagonic.core.formats.security import ZipConstants
from Pagonic.core.formats.zip_reader import ZipReader


def _make_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


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
    assert {
        "archive_path",
        "file_count",
        "total_compressed_size",
        "total_uncompressed_size",
        "global_compression_ratio",
        "risk_level",
        "risk_flags",
        "warnings",
        "errors",
        "recommended_action",
        "entries",
    }.issubset(payload)
    assert {
        "original_name",
        "normalized_name",
        "safe_name",
        "compressed_size",
        "uncompressed_size",
        "compression_method",
        "compression_ratio",
        "crc32",
        "risk_flags",
    }.issubset(payload["entries"][0])


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

    report = ZipReader(str(archive)).inspect()

    assert report.risk_level == "ok"
    assert report.entries[0].filename == "file.txt"
