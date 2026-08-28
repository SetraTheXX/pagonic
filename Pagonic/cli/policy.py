"""Explicit policy decisions for the automation-facing CLI workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from Pagonic.core.formats.inspection import ArchiveRisk


RiskLevel = Literal["ok", "low", "medium", "high", "critical"]
PolicyReason = Literal[
    "accepted",
    "validation_errors",
    "risk_exceeds_threshold",
    "unsupported_compression_method",
]

RISK_LEVEL_ORDER: dict[RiskLevel, int] = {
    "ok": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


@dataclass(frozen=True)
class InspectionPolicy:
    """Stable defaults for the inspection, verification, and extraction gates."""

    verify_max_risk: RiskLevel = "low"
    safe_extract_allow_risk: RiskLevel = "medium"

    def __post_init__(self) -> None:
        _validate_risk_level(self.verify_max_risk)
        _validate_risk_level(self.safe_extract_allow_risk)


@dataclass(frozen=True)
class PolicyDecision:
    """The reason and exit behavior produced by an inspection policy check."""

    allowed: bool
    reason: PolicyReason
    risk_level: RiskLevel
    threshold: RiskLevel

    @property
    def exit_code(self) -> int:
        """Return the documented automation exit code for this decision."""
        return 0 if self.allowed else 1


def evaluate_verification(report, policy: InspectionPolicy | None = None) -> PolicyDecision:
    """Evaluate the ``verify`` contract without changing the inspection report."""
    active_policy = policy or InspectionPolicy()
    return _evaluate_report(
        report,
        threshold=active_policy.verify_max_risk,
        reject_unsupported=False,
    )


def evaluate_safe_extraction(
    report,
    policy: InspectionPolicy | None = None,
) -> PolicyDecision:
    """Evaluate the ``safe-extract`` gate before any output path is created."""
    active_policy = policy or InspectionPolicy()
    return _evaluate_report(
        report,
        threshold=active_policy.safe_extract_allow_risk,
        reject_unsupported=True,
    )


def _evaluate_report(
    report,
    *,
    threshold: RiskLevel,
    reject_unsupported: bool,
) -> PolicyDecision:
    """Apply the stable precedence order shared by the CLI workflows."""
    active_threshold = _validate_risk_level(threshold)
    report_risk = _validate_risk_level(report.risk_level)

    if report.errors:
        return PolicyDecision(
            allowed=False,
            reason="validation_errors",
            risk_level=report_risk,
            threshold=active_threshold,
        )

    if RISK_LEVEL_ORDER[report_risk] > RISK_LEVEL_ORDER[active_threshold]:
        return PolicyDecision(
            allowed=False,
            reason="risk_exceeds_threshold",
            risk_level=report_risk,
            threshold=active_threshold,
        )

    if (
        reject_unsupported
        and ArchiveRisk.UNSUPPORTED_COMPRESSION_METHOD in report.risk_flags
    ):
        return PolicyDecision(
            allowed=False,
            reason="unsupported_compression_method",
            risk_level=report_risk,
            threshold=active_threshold,
        )

    return PolicyDecision(
        allowed=True,
        reason="accepted",
        risk_level=report_risk,
        threshold=active_threshold,
    )


def _validate_risk_level(value: str) -> RiskLevel:
    if value not in RISK_LEVEL_ORDER:
        raise ValueError(f"Unknown risk level: {value!r}")
    return cast(RiskLevel, value)


__all__ = [
    "InspectionPolicy",
    "PolicyDecision",
    "PolicyReason",
    "RISK_LEVEL_ORDER",
    "RiskLevel",
    "evaluate_safe_extraction",
    "evaluate_verification",
]
