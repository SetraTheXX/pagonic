from types import SimpleNamespace

import pytest

from Pagonic.cli.policy import (
    InspectionPolicy,
    evaluate_safe_extraction,
    evaluate_verification,
)


def test_default_policy_accepts_clean_archives_for_both_workflows():
    policy = InspectionPolicy()
    report = SimpleNamespace(
        risk_level="ok",
        risk_flags=[],
        errors=[],
    )

    assert policy.verify_max_risk == "low"
    assert policy.safe_extract_allow_risk == "medium"
    assert evaluate_verification(report, policy).allowed is True
    assert evaluate_safe_extraction(report, policy).allowed is True


def test_validation_errors_override_any_risk_threshold():
    policy = InspectionPolicy(
        verify_max_risk="critical",
        safe_extract_allow_risk="critical",
    )
    report = SimpleNamespace(
        risk_level="critical",
        risk_flags=["crc_or_structure_error"],
        errors=["Invalid or unreadable ZIP archive"],
    )

    verify_decision = evaluate_verification(report, policy)
    extract_decision = evaluate_safe_extraction(report, policy)

    assert verify_decision.allowed is False
    assert verify_decision.reason == "validation_errors"
    assert verify_decision.exit_code == 1
    assert extract_decision.allowed is False
    assert extract_decision.reason == "validation_errors"
    assert extract_decision.exit_code == 1


def test_unsupported_methods_are_thresholded_for_verify_but_block_extraction():
    report = SimpleNamespace(
        risk_level="medium",
        risk_flags=["unsupported_compression_method"],
        errors=[],
    )

    assert evaluate_verification(report).allowed is False
    assert evaluate_verification(
        report,
        InspectionPolicy(verify_max_risk="medium"),
    ).allowed is True

    extract_decision = evaluate_safe_extraction(
        report,
        InspectionPolicy(safe_extract_allow_risk="critical"),
    )
    assert extract_decision.allowed is False
    assert extract_decision.reason == "unsupported_compression_method"
    assert extract_decision.exit_code == 1


@pytest.mark.parametrize("field", ["verify_max_risk", "safe_extract_allow_risk"])
def test_policy_rejects_unknown_thresholds(field):
    with pytest.raises(ValueError, match="Unknown risk level"):
        InspectionPolicy(**{field: "unknown"})


def test_policy_rejects_unknown_report_risk_levels():
    report = SimpleNamespace(risk_level="unknown", risk_flags=[], errors=[])

    with pytest.raises(ValueError, match="Unknown risk level"):
        evaluate_verification(report)


@pytest.mark.parametrize(
    ("risk_level", "threshold", "allowed"),
    [
        ("ok", "ok", True),
        ("low", "low", True),
        ("medium", "low", False),
        ("medium", "medium", True),
        ("high", "medium", False),
        ("high", "high", True),
        ("critical", "high", False),
    ],
)
def test_verification_threshold_is_inclusive(risk_level, threshold, allowed):
    report = SimpleNamespace(risk_level=risk_level, risk_flags=[], errors=[])
    policy = InspectionPolicy(verify_max_risk=threshold)

    decision = evaluate_verification(report, policy)

    assert decision.allowed is allowed
    assert decision.reason == ("accepted" if allowed else "risk_exceeds_threshold")
    assert decision.exit_code == (0 if allowed else 1)


@pytest.mark.parametrize(
    ("risk_level", "threshold", "allowed"),
    [
        ("ok", "medium", True),
        ("low", "medium", True),
        ("medium", "medium", True),
        ("high", "medium", False),
        ("high", "high", True),
    ],
)
def test_safe_extraction_threshold_is_inclusive(risk_level, threshold, allowed):
    report = SimpleNamespace(risk_level=risk_level, risk_flags=[], errors=[])
    policy = InspectionPolicy(safe_extract_allow_risk=threshold)

    decision = evaluate_safe_extraction(report, policy)

    assert decision.allowed is allowed
    assert decision.reason == ("accepted" if allowed else "risk_exceeds_threshold")
    assert decision.exit_code == (0 if allowed else 1)
