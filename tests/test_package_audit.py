from pathlib import Path


def test_package_audit_records_contents_installation_and_no_publish_decision():
    repository_root = Path(__file__).resolve().parents[1]
    audit = (repository_root / "docs" / "package-audit.md").read_text(
        encoding="utf-8"
    )

    assert "# Package Surface Audit" in audit
    assert "pagonic-0.4.0-py3-none-any.whl" in audit
    assert "pagonic-0.4.0.tar.gz" in audit
    assert "do not publish" in audit
    assert "pip check" in audit
    assert "pagonic-gui" in audit
    assert "v0.5.0" in audit


def test_public_docs_link_the_package_audit_and_roadmap_records_the_decision():
    repository_root = Path(__file__).resolve().parents[1]
    readme = (repository_root / "README.md").read_text(encoding="utf-8")
    roadmap = (repository_root / "docs" / "roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "[Package Surface Audit](docs/package-audit.md)" in readme
    assert "[package surface audit](package-audit.md)" in roadmap
    assert "no PyPI or TestPyPI upload" in roadmap
