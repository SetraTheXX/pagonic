from pathlib import Path

from Pagonic import __version__
from Pagonic.core.formats.handlers.zip_handler import HANDLER_VERSION


def test_release_audit_records_the_0_5_release_decision_and_gates():
    repository_root = Path(__file__).resolve().parents[1]
    audit = (repository_root / "docs" / "release-audit-0.5.md").read_text(
        encoding="utf-8"
    )

    assert "# Pagonic v0.5.0 Release Audit" in audit
    assert "Tag: `v0.5.0`" in audit
    assert "PyPI/TestPyPI at audit time: not published" in audit
    assert "package-index publication" in audit
    assert "[x] Normal local test suite passes." in audit
    assert "[x] Windows/Linux CI passes for Python 3.10 through 3.13." in audit
    assert "no release-blocking bug or logic contradiction" in audit


def test_public_docs_identify_the_released_0_5_surface():
    repository_root = Path(__file__).resolve().parents[1]
    readme = (repository_root / "README.md").read_text(encoding="utf-8")
    roadmap = (repository_root / "docs" / "roadmap.md").read_text(encoding="utf-8")
    changelog = (repository_root / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "v0.5.0" in readme
    assert "[0.5 Release Audit](docs/release-audit-0.5.md)" in readme
    assert "0.5.0 Released Milestone" in roadmap
    assert "0.5.0 - Trustworthy inspection for automation" in changelog


def test_runtime_and_compatibility_versions_are_aligned():
    assert __version__ == "0.5.0"
    assert HANDLER_VERSION == __version__
