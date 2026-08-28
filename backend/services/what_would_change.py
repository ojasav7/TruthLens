"""'What Would Change My Mind?' Mode.

Identifies missing or unresolved information that could materially
change the investigation. Ranked by potential impact.
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.wwcm")


@dataclass
class MissingEvidence:
    priority: int
    description: str
    reason: str
    potential_impact: str  # HIGH, MEDIUM, LOW
    availability: str  # AVAILABLE, POSSIBLE, UNAVAILABLE

    def to_dict(self):
        return asdict(self)


def identify_missing_evidence(
    has_original_source: bool = False,
    has_provenance: bool = False,
    has_high_quality_audio: bool = True,
    has_independent_source: bool = False,
    has_fact_check: bool = False,
    has_cross_modal_match: bool = True,
    current_risk: float = 50.0,
) -> dict:
    """Identify what evidence could change the assessment."""
    missing = []
    priority = 1

    if not has_original_source:
        missing.append(MissingEvidence(
            priority=priority,
            description="Original source file",
            reason="High potential uncertainty reduction — original media enables full forensic re-analysis",
            potential_impact="HIGH",
            availability="POSSIBLE",
        ))
        priority += 1

    if not has_provenance:
        missing.append(MissingEvidence(
            priority=priority,
            description="Verified provenance (C2PA/XMP)",
            reason="Provenance chain would establish creation and modification history",
            potential_impact="HIGH",
            availability="POSSIBLE",
        ))
        priority += 1

    if not has_independent_source:
        missing.append(MissingEvidence(
            priority=priority,
            description="Independent source confirmation",
            reason="Corroboration from unrelated sources strengthens assessment reliability",
            potential_impact="HIGH",
            availability="POSSIBLE",
        ))
        priority += 1

    if not has_high_quality_audio:
        missing.append(MissingEvidence(
            priority=priority,
            description="Higher-quality audio recording",
            reason="Better audio enables more reliable voice clone detection",
            potential_impact="MEDIUM",
            availability="POSSIBLE",
        ))
        priority += 1

    if not has_fact_check:
        missing.append(MissingEvidence(
            priority=priority,
            description="Complete fact-check verification",
            reason="Claim verification provides independent assessment of content truthfulness",
            potential_impact="MEDIUM",
            availability="AVAILABLE",
        ))
        priority += 1

    if not has_cross_modal_match:
        missing.append(MissingEvidence(
            priority=priority,
            description="Cross-modal consistency resolution",
            reason="Audio/video temporal alignment would resolve cross-modal uncertainty",
            potential_impact="MEDIUM",
            availability="POSSIBLE",
        ))
        priority += 1

    current = "High manipulation risk" if current_risk >= 70 else "Moderate risk" if current_risk >= 30 else "Low detected risk"

    return {
        "current_assessment": current,
        "current_risk": current_risk,
        "missing_evidence": [m.to_dict() for m in missing],
        "total_missing": len(missing),
        "summary": f"{len(missing)} piece(s) of evidence could materially change this assessment.",
    }
