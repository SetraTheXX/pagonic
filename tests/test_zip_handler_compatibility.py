"""Contract tests for the legacy ZipHandler compatibility surface."""

from Pagonic import ZipHandler
from Pagonic.core.formats.handlers import register_zip_handler
from Pagonic.core.formats.zip_reader import ZipReader


def test_legacy_handler_public_contract_remains_available():
    handler = ZipHandler()

    assert handler.name == "zip"
    assert handler.extensions == [".zip"]
    assert handler.can_compress is True
    assert handler.can_decompress is True
    for method_name in ("compress", "decompress", "validate", "get_metadata"):
        assert callable(getattr(handler, method_name))


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
    assert result["success"] == ["payload.txt"]
    assert (output / "payload.txt").read_text(encoding="utf-8") == "compatibility contract"


def test_legacy_registration_returns_compatibility_handler():
    registered = register_zip_handler()

    assert isinstance(registered, ZipHandler)
    assert registered.name == "zip"
