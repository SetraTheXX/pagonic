import pytest
from click.testing import CliRunner

from Pagonic.cli.main import cli
from Pagonic.core.formats.inspection import ArchiveRisk, inspect_archive
from Pagonic.core.formats.security import ZipConstants

from .corpus import (
    build_absolute_path_fixture,
    build_case_collision_fixture,
    build_clean_fixture,
    build_corrupt_structure_fixture,
    build_duplicate_fixture,
    build_encrypted_fixture,
    build_high_ratio_fixture,
    build_large_uncompressed_fixture,
    build_long_metadata_fixture,
    build_nested_archive_fixture,
    build_normalized_collision_fixture,
    build_symlink_fixture,
    build_too_many_files_fixture,
    build_traversal_fixture,
    build_unsupported_method_fixture,
    build_unicode_collision_fixture,
)


def test_security_corpus_reports_mixed_separator_traversal(tmp_path):
    archive = build_traversal_fixture(tmp_path / "mixed-traversal.zip")

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.risk_flags == [ArchiveRisk.PATH_TRAVERSAL]
    assert report.entries[0].risk_flags == [ArchiveRisk.PATH_TRAVERSAL]


@pytest.mark.parametrize(
    ("builder", "expected_flags", "expected_entry_flags"),
    [
        (
            build_duplicate_fixture,
            [ArchiveRisk.DUPLICATE_FILENAME],
            [
                [ArchiveRisk.DUPLICATE_FILENAME],
                [ArchiveRisk.DUPLICATE_FILENAME],
            ],
        ),
        (
            build_normalized_collision_fixture,
            [
                ArchiveRisk.NORMALIZED_PATH_COLLISION,
                ArchiveRisk.CASE_INSENSITIVE_COLLISION,
                ArchiveRisk.UNICODE_NORMALIZATION_COLLISION,
            ],
            [
                [
                    ArchiveRisk.NORMALIZED_PATH_COLLISION,
                    ArchiveRisk.CASE_INSENSITIVE_COLLISION,
                    ArchiveRisk.UNICODE_NORMALIZATION_COLLISION,
                ],
                [
                    ArchiveRisk.NORMALIZED_PATH_COLLISION,
                    ArchiveRisk.CASE_INSENSITIVE_COLLISION,
                    ArchiveRisk.UNICODE_NORMALIZATION_COLLISION,
                ],
            ],
        ),
        (
            build_case_collision_fixture,
            [ArchiveRisk.CASE_INSENSITIVE_COLLISION],
            [
                [ArchiveRisk.CASE_INSENSITIVE_COLLISION],
                [ArchiveRisk.CASE_INSENSITIVE_COLLISION],
            ],
        ),
        (
            build_unicode_collision_fixture,
            [ArchiveRisk.UNICODE_NORMALIZATION_COLLISION],
            [
                [ArchiveRisk.UNICODE_NORMALIZATION_COLLISION],
                [ArchiveRisk.UNICODE_NORMALIZATION_COLLISION],
            ],
        ),
    ],
    ids=["duplicate", "normalized", "case-insensitive", "unicode"],
)
def test_security_corpus_reports_deterministic_collision_flags(
    tmp_path,
    builder,
    expected_flags,
    expected_entry_flags,
):
    archive = builder(tmp_path / "collision.zip")

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.risk_flags == expected_flags
    assert [entry.risk_flags for entry in report.entries] == expected_entry_flags


@pytest.mark.parametrize(
    ("builder", "expected_flags", "expected_level", "expected_errors"),
    [
        (
            build_absolute_path_fixture,
            [ArchiveRisk.ABSOLUTE_PATH, ArchiveRisk.WINDOWS_DRIVE_PATH],
            "high",
            False,
        ),
        (build_symlink_fixture, [ArchiveRisk.SYMLINK_ENTRY], "high", False),
        (build_encrypted_fixture, [ArchiveRisk.ENCRYPTED_ENTRY], "high", False),
        (
            build_unsupported_method_fixture,
            [ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD],
            "medium",
            False,
        ),
        (build_nested_archive_fixture, [ArchiveRisk.NESTED_ARCHIVE], "low", False),
        (
            build_long_metadata_fixture,
            [ArchiveRisk.LONG_FILENAME, ArchiveRisk.LONG_ARCHIVE_COMMENT],
            "medium",
            False,
        ),
        (
            build_corrupt_structure_fixture,
            [ArchiveRisk.CRC_OR_STRUCTURE_ERROR],
            "critical",
            True,
        ),
    ],
    ids=[
        "absolute-paths",
        "symlink-metadata",
        "encrypted-marker",
        "unsupported-method",
        "nested-archive",
        "long-metadata",
        "corrupt-structure",
    ],
)
def test_security_corpus_reports_metadata_and_structure_risks(
    tmp_path,
    builder,
    expected_flags,
    expected_level,
    expected_errors,
):
    if builder is build_unsupported_method_fixture:
        pytest.importorskip("bz2")

    archive = builder(tmp_path / "metadata.zip")

    report = inspect_archive(archive)

    assert report.risk_flags == expected_flags
    assert report.risk_level == expected_level
    assert bool(report.errors) is expected_errors


@pytest.mark.parametrize(
    ("builder", "constant", "limit", "expected_flag"),
    [
        (
            build_too_many_files_fixture,
            "MAX_FILES_IN_ZIP",
            2,
            ArchiveRisk.TOO_MANY_FILES,
        ),
        (
            build_large_uncompressed_fixture,
            "MAX_UNCOMPRESSED_SIZE",
            8,
            ArchiveRisk.LARGE_UNCOMPRESSED_SIZE,
        ),
        (
            build_high_ratio_fixture,
            "MAX_COMPRESSION_RATIO",
            2,
            ArchiveRisk.HIGH_COMPRESSION_RATIO,
        ),
    ],
    ids=["file-count-limit", "uncompressed-size-limit", "compression-ratio-limit"],
)
def test_security_corpus_reports_resource_limits(
    tmp_path,
    monkeypatch,
    builder,
    constant,
    limit,
    expected_flag,
):
    monkeypatch.setattr(ZipConstants, constant, limit)
    archive = builder(tmp_path / "resource-limit.zip")

    report = inspect_archive(archive)

    assert report.risk_level == "high"
    assert report.risk_flags == [expected_flag]


@pytest.mark.parametrize(
    ("builder", "constant", "limit"),
    [
        (build_too_many_files_fixture, "MAX_FILES_IN_ZIP", 2),
        (build_large_uncompressed_fixture, "MAX_UNCOMPRESSED_SIZE", 8),
        (build_high_ratio_fixture, "MAX_COMPRESSION_RATIO", 2),
    ],
    ids=["file-count-limit", "uncompressed-size-limit", "compression-ratio-limit"],
)
def test_safe_extract_refuses_resource_limit_corpus_without_output(
    tmp_path,
    monkeypatch,
    builder,
    constant,
    limit,
):
    monkeypatch.setattr(ZipConstants, constant, limit)
    archive = builder(tmp_path / "resource-unsafe.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(cli, ["safe-extract", str(archive), str(output)])

    assert result.exit_code == 1
    assert not output.exists()


@pytest.mark.parametrize(
    "builder",
    [
        build_traversal_fixture,
        build_absolute_path_fixture,
        build_duplicate_fixture,
        build_normalized_collision_fixture,
        build_case_collision_fixture,
        build_unicode_collision_fixture,
        build_symlink_fixture,
        build_encrypted_fixture,
        build_corrupt_structure_fixture,
    ],
    ids=[
        "traversal",
        "absolute-paths",
        "duplicate",
        "normalized-collision",
        "case-collision",
        "unicode-collision",
        "symlink",
        "encrypted",
        "corrupt",
    ],
)
def test_safe_extract_refuses_high_risk_corpus_without_creating_output(
    tmp_path,
    builder,
):
    archive = builder(tmp_path / "unsafe.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(cli, ["safe-extract", str(archive), str(output)])

    assert result.exit_code == 1
    assert not output.exists()


def test_safe_extract_refuses_unsupported_method_corpus_without_output(tmp_path):
    pytest.importorskip("bz2")
    archive = build_unsupported_method_fixture(tmp_path / "unsupported.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(cli, ["safe-extract", str(archive), str(output)])

    assert result.exit_code == 1
    assert "unsupported_compression_method" in result.output
    assert not output.exists()


def test_safe_extract_writes_only_the_clean_corpus_payload(tmp_path):
    archive = build_clean_fixture(tmp_path / "clean.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(cli, ["safe-extract", str(archive), str(output)])

    assert result.exit_code == 0
    assert (output / "docs" / "readme.txt").read_bytes() == b"synthetic clean payload"


def test_safe_extract_can_preview_nested_corpus_without_writing(tmp_path):
    archive = build_nested_archive_fixture(tmp_path / "nested.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(
        cli,
        ["safe-extract", str(archive), str(output), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Dry run OK" in result.output
    assert not output.exists()


def test_safe_extract_previews_long_metadata_without_host_filesystem_dependency(tmp_path):
    archive = build_long_metadata_fixture(tmp_path / "long.zip")
    output = tmp_path / "out"

    result = CliRunner().invoke(
        cli,
        ["safe-extract", str(archive), str(output), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Dry run OK" in result.output
    assert not output.exists()
