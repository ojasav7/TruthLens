"""'Why Not Certain?' Panel.

Every important assessment explains remaining uncertainty.
Generated only from actual unresolved signals — never invented.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.why_not")


@dataclass
class UncertaintyReason:
    reason: str
    category: str  # source, provenance, model, evidence, quality
    impact: str  # HIGH, MEDIUM, LOW

    def to_dict(self):
        return asdict(self)


def generate_uncertainty_reasons(
    source_available: bool = True,
    provenance_available: bool = False,
    model_agreement: bool = True,
    fact_check_complete: bool = False,
    audio_quality_sufficient: bool = True,
    evidence_count: int = 0,
    contradiction_count: int = 0,
    original_source_available: bool = False,
) -> dict:
    """Generate 'Why Not Certain?' from actual system state."""
    reasons = []

    if not original_source_available:
        reasons.append(UncertaintyReason(
            reason="Original source file unavailable",
            category="source",
            impact="HIGH",
        ))

    if not provenance_available:
        reasons.append(UncertaintyReason(
            reason="Provenance/C2PA data not available",
            category="provenance",
            impact="HIGH",
        ))

    if not model_agreement:
        reasons.append(UncertaintyReason(
            reason="Models disagree on assessment",
            category="model",
            impact="HIGH",
        ))

    if not fact_check_complete:
        reasons.append(UncertaintyReason(
            reason="Fact-check result incomplete or unavailable",
            category="evidence",
            impact="MEDIUM",
        ))

    if not audio_quality_sufficient:
        reasons.append(UncertaintyReason(
            reason="Audio quality insufficient for reliable analysis",
            category="quality",
            impact="MEDIUM",
        ))

    if evidence_count < 2:
        reasons.append(UncertaintyReason(
            reason="Limited independent evidence available",
            category="evidence",
            impact="MEDIUM",
        ))

    if contradiction_count > 0:
        reasons.append(UncertaintyReason(
            reason=f"{contradiction_count} contradicting evidence item(s) present",
            category="evidence",
            impact="HIGH" if contradiction_count >= 2 else "MEDIUM",
        ))

    if not reasons:
        return {
            "has_uncertainty": False,
            "reasons": [],
            "summary": "No major unresolved evidence limitations were identified.",
        }

    return {
        "has_uncertainty": True,
        "reasons": [r.to_dict() for r in reasons],
        "summary": f"{len(reasons)} unresolved limitation(s) affect certainty.",
    }
