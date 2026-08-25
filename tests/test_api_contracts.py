"""Public API contract tests for the 0.4 polish surface."""

from typing import get_type_hints

from Pagonic import (
    ArchiveInfo,
    CompressionStats,
    ExtractionResult,
    FileInfo,
)
from Pagonic.core.formats.zip_reader import ZipReader
from Pagonic.core.formats.zip_writer import ZipWriter
from Pagonic.core.config_manager import ConfigManager


def test_zip_operation_return_contracts_are_public_and_typed():
    reader_info = get_type_hints(ZipReader.get_archive_info)
    reader_extract = get_type_hints(ZipReader.extract_all)
    writer_finalize = get_type_hints(ZipWriter.finalize)

    assert reader_info["return"] is ArchiveInfo
    assert reader_extract["return"] is ExtractionResult
    assert writer_finalize["return"] is CompressionStats

    assert set(FileInfo.__annotations__) == {
        "filename",
        "compressed_size",
        "uncompressed_size",
        "compression_method",
        "crc32",
    }


def test_config_manager_isolates_mutable_defaults_and_recent_files(tmp_path):
    first = ConfigManager(tmp_path / "one.json")
    second = ConfigManager(tmp_path / "two.json")

    first.add_recent_file("one.zip")

    assert first.get_recent_files() == ["one.zip"]
    assert second.get_recent_files() == []

    recent_files = first.get_recent_files()
    recent_files.append("outside.zip")

    assert first.get_recent_files() == ["one.zip"]

    snapshot = first.to_dict()
    snapshot["recent_files"].append("snapshot.zip")

    assert first.get_recent_files() == ["one.zip"]


def test_zip_result_mappings_keep_stable_runtime_shapes(tmp_path):
    archive_path = tmp_path / "sample.zip"
    output_dir = tmp_path / "out"

    writer = ZipWriter(str(archive_path))
    writer.add_data("hello.txt", b"hello")
    stats = writer.finalize()

    assert set(stats) == {
        "backend",
        "files_processed",
        "total_compressed_size",
        "total_uncompressed_size",
        "compression_ratio",
    }

    reader = ZipReader(str(archive_path))
    info = reader.get_archive_info()
    file_info = reader.get_file_info("hello.txt")
    extraction = reader.extract_all(str(output_dir))

    assert set(info) == {
        "path",
        "file_count",
        "total_compressed_size",
        "total_uncompressed_size",
        "compression_ratio",
    }
    assert set(file_info or {}) == set(FileInfo.__annotations__)
    assert set(extraction) == {"total_entries", "success", "failed"}
    assert extraction["success"] == ["hello.txt"]
    assert extraction["failed"] == []
