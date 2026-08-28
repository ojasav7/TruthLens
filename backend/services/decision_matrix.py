"""Final Decision Matrix.

Deterministic decision layer on top of all signals.
Never claims certainty — uses terms like "assessment", "recommendation".
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.decision")


@dataclass
class DecisionResult:
    assessment: str  # HIGH RISK, REVIEW REQUIRED, LOW RISK, INCONCLUSIVE
    risk_level: str  # HIGH, MEDIUM, LOW
    evidence_level: str  # STRONG, MODERATE, WEAK, INSUFFICIENT
    uncertainty_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    agreement_level: str  # HIGH, MODERATE, LOW, DISAGREEMENT
    confidence: str  # HIGH, MEDIUM, LOW
    rationale: str

    def to_dict(self):
        return asdict(self)


def make_decision(
    risk_score: float,
    evidence_strength: float,
    uncertainty_level: str = "MEDIUM",
    agreement: str = "MODERATE_AGREEMENT",
    model_confidence: float = 0.5,
) -> dict:
    """Deterministic decision based on all available signals."""

    # Classify inputs
    risk = "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 30 else "LOW"
    evidence = "STRONG" if evidence_strength >= 0.7 else "MODERATE" if evidence_strength >= 0.4 else "WEAK" if evidence_strength >= 0.2 else "INSUFFICIENT"
    agreement_label = _classify_agreement(agreement)
    conf = "HIGH" if model_confidence >= 0.75 else "MEDIUM" if model_confidence >= 0.5 else "LOW"

    # Decision logic
    if risk == "HIGH" and evidence in ("STRONG", "MODERATE"):
        assessment = "HIGH RISK"
        rationale = f"Risk {risk_score:.0f} with {evidence.lower()} evidence supports high-risk classification"
    elif risk == "HIGH" and evidence in ("WEAK", "INSUFFICIENT"):
        assessment = "REVIEW REQUIRED"
        rationale = f"Risk {risk_score:.0f} detected but evidence is {evidence.lower()} — needs human review"
    elif risk == "LOW" and evidence in ("STRONG", "MODERATE"):
        assessment = "LOW RISK"
        rationale = f"Risk {risk_score:.0f} with {evidence.lower()} evidence supports low-risk classification"
    elif risk == "LOW" and evidence in ("WEAK", "INSUFFICIENT"):
        assessment = "REVIEW REQUIRED"
        rationale = f"Risk appears low but evidence is insufficient — review recommended"
    elif uncertainty_level in ("HIGH", "CRITICAL"):
        assessment = "INCONCLUSIVE"
        rationale = f"Uncertainty is {uncertainty_level} — cannot make reliable determination"
    else:
        assessment = "REVIEW REQUIRED"
        rationale = f"Mixed signals: risk={risk}, evidence={evidence}, uncertainty={uncertainty_level}"

    return DecisionResult(
        assessment=assessment,
        risk_level=risk,
        evidence_level=evidence,
        uncertainty_level=uncertainty_level,
        agreement_level=agreement_label,
        confidence=conf,
        rationale=rationale,
    ).to_dict()


def _classify_agreement(agreement: str) -> str:
    mapping = {
        "HIGH_AGREEMENT": "HIGH",
        "MODERATE_AGREEMENT": "MODERATE",
        "LOW_AGREEMENT": "LOW",
        "STRONG_DISAGREEMENT": "DISAGREEMENT",
    }
    return mapping.get(agreement, "UNKNOWN")
