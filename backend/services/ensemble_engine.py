"""Second Opinion / Ensemble Engine.

Compares independent model signals before producing a final assessment.
Additive — does NOT replace the current model.
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.ensemble")


@dataclass
class ModelSignal:
    model_id: str
    model_version: str
    label: str  # "real", "fake", "cloned"
    confidence: float  # 0-1


@dataclass
class EnsembleResult:
    agreement: str  # HIGH_AGREEMENT, MODERATE_AGREEMENT, LOW_AGREEMENT, STRONG_DISAGREEMENT
    confidence_diff: float
    score_variance: float
    ensemble_confidence: float
    disagreement_severity: str  # NONE, LOW, MEDIUM, HIGH
    signals: list = field(default_factory=list)
    needs_human_review: bool = False

    def to_dict(self):
        return asdict(self)


def compute_ensemble(signals: list[ModelSignal]) -> EnsembleResult:
    """Compare model signals and compute ensemble metrics."""
    if len(signals) < 2:
        return EnsembleResult(
            agreement="SINGLE_MODEL",
            confidence_diff=0.0,
            score_variance=0.0,
            ensemble_confidence=signals[0].confidence if signals else 0.0,
            disagreement_severity="NONE",
            signals=[asdict(s) for s in signals],
        )

    # Label agreement
    labels = [s.label for s in signals]
    label_agreement = len(set(labels)) == 1

    # Confidence difference
    confidences = [s.confidence for s in signals]
    conf_diff = max(confidences) - min(confidences)

    # Score variance
    mean_c = sum(confidences) / len(confidences)
    score_var = sum((c - mean_c) ** 2 for c in confidences) / len(confidences)

    # Ensemble confidence: weighted average favoring higher confidence
    total = sum(confidences)
    ensemble_conf = sum(c * c for c in confidences) / total if total > 0 else 0.0

    # Agreement level
    if label_agreement and conf_diff < 0.1:
        agreement = "HIGH_AGREEMENT"
        severity = "NONE"
    elif label_agreement and conf_diff < 0.25:
        agreement = "MODERATE_AGREEMENT"
        severity = "LOW"
    elif label_agreement:
        agreement = "LOW_AGREEMENT"
        severity = "MEDIUM"
    else:
        agreement = "STRONG_DISAGREEMENT"
        severity = "HIGH"

    needs_review = severity in ("MEDIUM", "HIGH") or conf_diff > 0.3

    result = EnsembleResult(
        agreement=agreement,
        confidence_diff=round(conf_diff, 4),
        score_variance=round(score_var, 4),
        ensemble_confidence=round(ensemble_conf, 4),
        disagreement_severity=severity,
        signals=[asdict(s) for s in signals],
        needs_human_review=needs_review,
    )

    if needs_review:
        logger.warning("Ensemble: disagreement detected — flagged for human review")

    return result


def get_second_opinion(primary: dict, secondary: dict) -> dict:
    """High-level API: take two prediction dicts, return ensemble analysis."""
    sig1 = ModelSignal(
        model_id=primary.get("model_id", "primary"),
        model_version=primary.get("model_version", "unknown"),
        label=primary.get("label", "unknown"),
        confidence=primary.get("confidence", 0.0),
    )
    sig2 = ModelSignal(
        model_id=secondary.get("model_id", "secondary"),
        model_version=secondary.get("model_version", "unknown"),
        label=secondary.get("label", "unknown"),
        confidence=secondary.get("confidence", 0.0),
    )
    return compute_ensemble([sig1, sig2]).to_dict()
