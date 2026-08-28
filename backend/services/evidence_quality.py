"""Evidence Quality Score.

Separate metric from model confidence: considers independent sources,
reliability, agreement, completeness, provenance, and consistency.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.evidence_quality")


@dataclass
class EvidenceQualityResult:
    score: float  # 0-100
    grade: str  # A, B, C, D, F
    factors: dict
    summary: str

    def to_dict(self):
        return asdict(self)


def compute_evidence_quality(
    num_sources: int = 0,
    source_reliability: float = 0.5,
    agreement: float = 0.5,
    completeness: float = 0.5,
    provenance_available: bool = False,
    has_contradictions: bool = False,
) -> EvidenceQualityResult:
    """Compute evidence quality from multiple factors."""
    factors = {}

    # Number of independent sources (0-25 points)
    src_score = min(num_sources * 8, 25)
    factors["source_count"] = {"value": num_sources, "points": src_score, "max": 25}

    # Source reliability (0-20 points)
    rel_score = source_reliability * 20
    factors["source_reliability"] = {"value": source_reliability, "points": round(rel_score, 1), "max": 20}

    # Agreement (0-25 points)
    agr_score = agreement * 25
    factors["agreement"] = {"value": agreement, "points": round(agr_score, 1), "max": 25}

    # Completeness (0-15 points)
    comp_score = completeness * 15
    factors["completeness"] = {"value": completeness, "points": round(comp_score, 1), "max": 15}

    # Provenance (0-15 points)
    prov_score = 15 if provenance_available else 0
    factors["provenance"] = {"value": provenance_available, "points": prov_score, "max": 15}

    # Penalty for contradictions (-10 points)
    contra_penalty = -10 if has_contradictions else 0
    factors["contradictions"] = {"value": has_contradictions, "penalty": contra_penalty}

    total = src_score + rel_score + agr_score + comp_score + prov_score + contra_penalty
    total = max(0, min(100, total))

    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 60:
        grade = "B"
    elif total >= 40:
        grade = "C"
    elif total >= 20:
        grade = "D"
    else:
        grade = "F"

    summary = _build_summary(num_sources, agreement, provenance_available, has_contradictions)

    return EvidenceQualityResult(
        score=round(total, 1),
        grade=grade,
        factors=factors,
        summary=summary,
    )


def _build_summary(num_sources: int, agreement: float, provenance: bool, contradictions: bool) -> str:
    parts = []
    if num_sources == 0:
        parts.append("No independent evidence sources")
    elif num_sources == 1:
        parts.append("Only one evidence source")
    else:
        parts.append(f"{num_sources} independent sources")

    if agreement < 0.3:
        parts.append("sources strongly disagree")
    elif agreement < 0.6:
        parts.append("mixed agreement among sources")

    if not provenance:
        parts.append("provenance unavailable")
    if contradictions:
        parts.append("contradictions detected")

    return "; ".join(parts) if parts else "Evidence quality is adequate"
