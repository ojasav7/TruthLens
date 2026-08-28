"""Verdict Consistency Checker.

Deterministic quality-control layer: verifies that risk score, confidence,
evidence, and verdict are aligned before publishing.
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.consistency")


@dataclass
class ConsistencyCheck:
    check_name: str
    passed: bool
    detail: str


@dataclass
class ConsistencyResult:
    is_consistent: bool
    checks: list[dict] = field(default_factory=list)
    suggested_verdict: str | None = None

    def to_dict(self):
        return asdict(self)


def check_verdict_consistency(
    risk_score: float,
    verdict: str,
    confidence: float,
    evidence_strength: float | None = None,
    uncertainty_level: str | None = None,
) -> ConsistencyResult:
    """Run deterministic consistency checks on the assessment."""
    checks = []

    # 1. Risk / Verdict alignment
    expected = _verdict_from_risk(risk_score)
    aligned = expected == verdict
    checks.append(ConsistencyCheck(
        check_name="risk_verdict_alignment",
        passed=aligned,
        detail=f"Risk {risk_score:.0f} suggests '{expected}' but verdict is '{verdict}'",
    ))

    # 2. Confidence / Verdict alignment
    if confidence < 0.3 and verdict == "High Risk":
        checks.append(ConsistencyCheck(
            check_name="confidence_verdict_alignment",
            passed=False,
            detail=f"Low confidence ({confidence:.0%}) but verdict is High Risk",
        ))
    elif confidence > 0.85 and verdict == "Low":
        # High confidence + low risk is fine
        checks.append(ConsistencyCheck(
            check_name="confidence_verdict_alignment",
            passed=True,
            detail=f"High confidence ({confidence:.0%}) consistent with Low verdict",
        ))
    else:
        checks.append(ConsistencyCheck(
            check_name="confidence_verdict_alignment",
            passed=True,
            detail=f"Confidence {confidence:.0%} consistent with {verdict}",
        ))

    # 3. Uncertainty / Review alignment
    if uncertainty_level in ("HIGH", "CRITICAL") and verdict in ("Low", "High Risk"):
        checks.append(ConsistencyCheck(
            check_name="uncertainty_review_alignment",
            passed=False,
            detail=f"Uncertainty is {uncertainty_level} but verdict is definitive ({verdict})",
        ))
    else:
        checks.append(ConsistencyCheck(
            check_name="uncertainty_review_alignment",
            passed=True,
            detail=f"Uncertainty {uncertainty_level or 'unknown'} consistent with {verdict}",
        ))

    # 4. Evidence / Verdict alignment
    if evidence_strength is not None:
        if evidence_strength < 0.2 and verdict == "High Risk":
            checks.append(ConsistencyCheck(
                check_name="evidence_verdict_alignment",
                passed=False,
                detail=f"Very weak evidence ({evidence_strength:.0%}) but verdict is High Risk",
            ))
        elif evidence_strength > 0.7 and verdict == "Review Needed":
            checks.append(ConsistencyCheck(
                check_name="evidence_verdict_alignment",
                passed=False,
                detail=f"Strong evidence ({evidence_strength:.0%}) but verdict is Review Needed",
            ))
        else:
            checks.append(ConsistencyCheck(
                check_name="evidence_verdict_alignment",
                passed=True,
                detail=f"Evidence {evidence_strength:.0%} consistent with {verdict}",
            ))

    all_passed = all(c.passed for c in checks)
    suggested = None if all_passed else _verdict_from_risk(risk_score)

    if not all_passed:
        logger.warning("Verdict inconsistency detected: %s", [c.detail for c in checks if not c.passed])

    return ConsistencyResult(
        is_consistent=all_passed,
        checks=[asdict(c) for c in checks],
        suggested_verdict=suggested,
    )


def _verdict_from_risk(score: float) -> str:
    if score >= 70:
        return "High Risk"
    elif score >= 30:
        return "Review Needed"
    return "Low"
