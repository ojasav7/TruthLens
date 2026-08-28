"""Uncertainty Engine.

Introduces explicit uncertainty measurement from multiple signals:
model disagreement, low confidence, missing evidence, conflicting evidence,
insufficient modality coverage, etc.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.uncertainty")


@dataclass
class UncertaintyResult:
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    score: float  # 0-1 (higher = more uncertain)
    sources: list[str]
    recommendation: str

    def to_dict(self):
        return asdict(self)


def compute_uncertainty(
    risk_score: float = 50.0,
    model_confidence: float = 0.5,
    evidence_strength: float = 0.5,
    evidence_agreement: float = 0.5,
    modality_count: int = 0,
    ensemble_disagreement: str = "NONE",
    provenance_available: bool = False,
    fact_check_available: bool = False,
) -> UncertaintyResult:
    """Compute uncertainty from multiple signals. Each input 0-1 except risk_score (0-100)."""
    sources = []
    uncertainty_signals = 0.0
    total_weight = 0.0

    # Model disagreement (weight: 0.25)
    w = 0.25
    total_weight += w
    if ensemble_disagreement == "HIGH":
        uncertainty_signals += w * 1.0
        sources.append("Models disagree strongly")
    elif ensemble_disagreement == "MEDIUM":
        uncertainty_signals += w * 0.6
        sources.append("Models show moderate disagreement")
    elif ensemble_disagreement == "LOW":
        uncertainty_signals += w * 0.2

    # Low model confidence (weight: 0.2)
    w = 0.2
    total_weight += w
    if model_confidence < 0.3:
        uncertainty_signals += w * 1.0
        sources.append("Very low model confidence")
    elif model_confidence < 0.5:
        uncertainty_signals += w * 0.5
        sources.append("Low model confidence")

    # Evidence strength (weight: 0.2)
    w = 0.2
    total_weight += w
    if evidence_strength < 0.2:
        uncertainty_signals += w * 1.0
        sources.append("Very weak evidence strength")
    elif evidence_strength < 0.4:
        uncertainty_signals += w * 0.5
        sources.append("Weak evidence strength")

    # Evidence agreement (weight: 0.15)
    w = 0.15
    total_weight += w
    if evidence_agreement < 0.3:
        uncertainty_signals += w * 1.0
        sources.append("Evidence sources conflict")
    elif evidence_agreement < 0.5:
        uncertainty_signals += w * 0.5
        sources.append("Mixed evidence agreement")

    # Modality coverage (weight: 0.1)
    w = 0.1
    total_weight += w
    if modality_count == 0:
        uncertainty_signals += w * 1.0
        sources.append("No modality data available")
    elif modality_count == 1:
        uncertainty_signals += w * 0.3
        sources.append("Single modality analyzed")

    # Missing provenance/fact-check (weight: 0.1)
    w = 0.1
    total_weight += w
    if not provenance_available and not fact_check_available:
        uncertainty_signals += w * 1.0
        sources.append("No provenance or fact-check data")
    elif not provenance_available:
        uncertainty_signals += w * 0.4
        sources.append("Provenance not available")

    # Normalize
    raw = uncertainty_signals / total_weight if total_weight > 0 else 0.5

    # Determine level
    if raw < 0.2:
        level = "LOW"
    elif raw < 0.45:
        level = "MEDIUM"
    elif raw < 0.7:
        level = "HIGH"
    else:
        level = "CRITICAL"

    # Decision matrix recommendation
    high_risk = risk_score >= 70
    high_evidence = evidence_strength >= 0.6

    if high_risk and high_evidence:
        recommendation = "HIGH RISK — high confidence assessment"
    elif high_risk and not high_evidence:
        recommendation = "REVIEW REQUIRED — risk detected but evidence insufficient"
    elif not high_risk and high_evidence:
        recommendation = "LOW RISK — well-supported assessment"
    else:
        recommendation = "REVIEW REQUIRED — both risk and evidence are ambiguous"

    if level == "CRITICAL":
        recommendation = "MANUAL REVIEW REQUIRED — uncertainty too high for automated assessment"

    return UncertaintyResult(
        level=level,
        score=round(raw, 4),
        sources=sources,
        recommendation=recommendation,
    )
