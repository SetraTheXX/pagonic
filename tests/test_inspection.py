import json
import zipfile

from Pagonic.core.formats.inspection import ArchiveRisk, inspect_archive
from Pagonic.core.formats.zip_reader import ZipReader


def _make_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def test_inspect_clean_archive_reports_ok(tmp_path):
    archive = tmp_path / "clean.zip"
    _make_zip(archive, {"docs/readme.txt": b"hello", "nested/file.txt": b"world"})

    report = inspect_archive(archive)

    assert report.risk_level == "ok"
    assert report.file_count == 2
    assert report.errors == []
    assert [entry.safe_path for entry in report.entries] == ["docs/readme.txt", "nested/file.txt"]
    json.dumps(report.to_dict())


def test_inspect_reports_path_traversal(tmp_path):
    archive = tmp_path / "traversal.zip"
    _make_zip(archive, {"../../evil.txt": b"nope"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.entries[0].safe_path == "evil.txt"
    assert ArchiveRisk.PATH_TRAVERSAL in report.entries[0].risk_flags


def test_inspect_reports_mixed_separator_traversal(tmp_path):
    archive = tmp_path / "mixed.zip"
    _make_zip(archive, {r"..\../safe/evil.txt": b"nope"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.entries[0].safe_path == "safe/evil.txt"
    assert ArchiveRisk.PATH_TRAVERSAL in report.entries[0].risk_flags


def test_inspect_reports_windows_absolute_path(tmp_path):
    archive = tmp_path / "windows-absolute.zip"
    _make_zip(archive, {r"C:\Users\Admin\file.doc": b"data"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.entries[0].safe_path == "Users/Admin/file.doc"
    assert ArchiveRisk.WINDOWS_DRIVE_PATH in report.entries[0].risk_flags


def test_inspect_reports_posix_absolute_path(tmp_path):
    archive = tmp_path / "posix-absolute.zip"
    _make_zip(archive, {"/etc/passwd": b"root"})

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.entries[0].safe_path == "etc/passwd"
    assert ArchiveRisk.ABSOLUTE_PATH in report.entries[0].risk_flags


def test_inspect_reports_hidden_filename(tmp_path):
    archive = tmp_path / "hidden.zip"
    _make_zip(archive, {".env": b"SECRET=value"})

    report = inspect_archive(archive)

    assert report.risk_level == "low"
    assert ArchiveRisk.HIDDEN_FILE in report.entries[0].risk_flags


def test_inspect_reports_suspicious_extension(tmp_path):
    archive = tmp_path / "suspicious.zip"
    _make_zip(archive, {"payload.exe": b"MZ"})

    report = inspect_archive(archive)

    assert report.risk_level == "medium"
    assert ArchiveRisk.SUSPICIOUS_EXTENSION in report.entries[0].risk_flags


def test_inspect_corrupt_archive_returns_critical_report(tmp_path):
    archive = tmp_path / "broken.zip"
    archive.write_bytes(b"not a real zip")

    report = inspect_archive(archive)

    assert report.risk_level == "critical"
    assert report.file_count == 0
    assert report.errors


def test_zip_reader_inspect_delegates_to_inspection_service(tmp_path):
    archive = tmp_path / "reader.zip"
    _make_zip(archive, {"file.txt": b"hello"})

    report = ZipReader(str(archive)).inspect()

    assert report.risk_level == "ok"
    assert report.entries[0].filename == "file.txt"
