"""Contract tests for the legacy ZipHandler compatibility surface."""

import warnings
from pathlib import Path

from Pagonic import ZipHandler
from Pagonic.core.formats.handlers import register_zip_handler
from Pagonic.core.formats.zip_reader import ZipReader


def test_legacy_handler_public_contract_remains_available():
    handler = ZipHandler()

    assert handler.name == "zip"
    assert handler.extensions == [".zip"]
    assert handler.can_compress is True
    assert handler.can_decompress is True
    for method_name in (
        "compress",
        "decompress",
        "validate",
        "get_metadata",
        "get_compression_ratio",
        "compress_file",
        "compress_file_with_threading",
        "compress_file_adaptive_memory",
        "compress_file_adaptive_memory_enhanced",
    ):
        assert callable(getattr(handler, method_name))


def test_0_5_compatibility_policy_does_not_add_deprecation_warning():
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        ZipHandler()

    assert not any(
        warning.category is DeprecationWarning for warning in captured
    )


def test_legacy_handler_roundtrip_is_readable_by_public_reader(tmp_path):
    source = tmp_path / "payload.txt"
    source.write_text("compatibility contract", encoding="utf-8")
    archive = tmp_path / "payload.zip"
    output = tmp_path / "output"

    handler = ZipHandler()
    handler.compress([str(source)], str(archive))

    report = ZipReader(str(archive)).inspect()
    assert report.risk_level == "ok"
    assert [entry.original_name for entry in report.entries] == ["payload.txt"]

    result = handler.decompress(str(archive), str(output))
    assert {"total_entries", "success", "failed"}.issubset(result)
    assert "error" not in result
    assert result["success"] == ["payload.txt"]
    assert (output / "payload.txt").read_text(encoding="utf-8") == "compatibility contract"


def test_legacy_registration_returns_compatibility_handler():
    registered = register_zip_handler()

    assert isinstance(registered, ZipHandler)
    assert registered.name == "zip"


def test_0_5_compatibility_policy_is_documented_for_migration():
    repository_root = Path(__file__).resolve().parents[1]
    policy = (repository_root / "docs" / "zip-handler-compatibility.md").read_text(
        encoding="utf-8"
    )
    migration = (repository_root / "docs" / "migration-0.4.md").read_text(
        encoding="utf-8"
    )
    roadmap = (repository_root / "docs" / "roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "behaviorally unchanged" in policy
    assert "does not add a new `DeprecationWarning`" in migration
    assert "breaking-release compatibility and deprecation path" in roadmap
