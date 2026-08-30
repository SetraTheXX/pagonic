from pathlib import Path

from Pagonic.core.formats.inspection import RISK_CATALOG


def test_sarif_evaluation_records_a_deferred_implementation_decision():
    repository_root = Path(__file__).resolve().parents[1]
    evaluation = (repository_root / "docs" / "sarif-evaluation.md").read_text(
        encoding="utf-8"
    )

    assert "defer implementation beyond 0.5" in evaluation
    assert "ruleId" in evaluation
    assert "security-events: write" in evaluation
    assert "inspect --sarif" in evaluation
    assert "No part of this slice is accepted or implemented" in evaluation
    for risk_id in RISK_CATALOG:
        assert f"`{risk_id}`" in evaluation


def test_sarif_evaluation_preserves_json_and_policy_boundaries():
    repository_root = Path(__file__).resolve().parents[1]
    evaluation = (repository_root / "docs" / "sarif-evaluation.md").read_text(
        encoding="utf-8"
    )

    assert "existing JSON inspection schema untouched" in evaluation
    assert "Consumers must continue to use `verify` or `safe-extract`" in evaluation
    assert "Never copy a machine-local absolute `archive_path`" in evaluation
