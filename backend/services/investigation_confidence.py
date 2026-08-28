"""Investigation Confidence.

Separate metric from model confidence. Uses a documented scoring method
considering: model agreement, evidence quality, source diversity, provenance,
claim verification, cross-modal agreement, contradiction level, missing evidence,
reproducibility, and data quality.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.inv_confidence")


@dataclass
class InvestigationConfidenceResult:
    score: float  # 0-100
    level: str  # HIGH, MEDIUM, LOW, INSUFFICIENT
    factors: dict
    summary: str

    def to_dict(self):
        return asdict(self)


# Weighted factors — total = 100
_WEIGHTS = {
    "model_agreement": 15,
    "evidence_quality": 20,
    "source_diversity": 10,
    "provenance": 15,
    "claim_verification": 10,
    "cross_modal_agreement": 10,
    "contradiction_level": 10,  # inverted: fewer contradictions = higher
    "data_quality": 10,
}


def compute_investigation_confidence(
    model_agreement: float = 0.5,       # 0-1
    evidence_quality: float = 0.5,       # 0-1
    source_diversity: float = 0.5,       # 0-1
    provenance_available: bool = False,  # bool
    claim_verification: float = 0.5,     # 0-1
    cross_modal_agreement: float = 0.5,  # 0-1
    contradiction_level: float = 0.0,    # 0-1 (0 = no contradictions)
    data_quality: float = 0.5,           # 0-1
) -> dict:
    """Compute investigation confidence from weighted factors."""
    factors = {}
    total = 0.0

    raw = {
        "model_agreement": model_agreement,
        "evidence_quality": evidence_quality,
        "source_diversity": source_diversity,
        "provenance": 1.0 if provenance_available else 0.0,
        "claim_verification": claim_verification,
        "cross_modal_agreement": cross_modal_agreement,
        "contradiction_level": 1.0 - contradiction_level,  # invert
        "data_quality": data_quality,
    }

    for factor, weight in _WEIGHTS.items():
        value = raw.get(factor, 0.5)
        points = value * weight
        total += points
        factors[factor] = {
            "value": round(value, 3),
            "weight": weight,
            "points": round(points, 1),
        }

    total = max(0, min(100, total))

    if total >= 75:
        level = "HIGH"
    elif total >= 50:
        level = "MEDIUM"
    elif total >= 25:
        level = "LOW"
    else:
        level = "INSUFFICIENT"

    summary_parts = []
    if evidence_quality < 0.3:
        summary_parts.append("evidence quality is weak")
    if contradiction_level > 0.5:
        summary_parts.append("significant contradictions present")
    if not provenance_available:
        summary_parts.append("provenance not verified")
    if model_agreement < 0.4:
        summary_parts.append("models show disagreement")
    if cross_modal_agreement < 0.4:
        summary_parts.append("cross-modal signals conflict")

    summary = "; ".join(summary_parts) if summary_parts else "Investigation confidence is adequate"

    return InvestigationConfidenceResult(
        score=round(total, 1),
        level=level,
        factors=factors,
        summary=summary,
    ).to_dict()
