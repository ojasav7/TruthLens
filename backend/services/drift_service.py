"""Model Drift Detection.

Monitors when real-world inputs begin differing from the training baseline.
Reports warnings, never auto-retrains.
"""

import logging
from dataclasses import dataclass, field, asdict
from collections import Counter

logger = logging.getLogger("truthlens.drift")

# Baseline distributions (updated periodically)
_baseline = {
    "confidence_distribution": {"mean": 0.7, "std": 0.15},
    "prediction_distribution": {"real": 0.55, "fake": 0.45},
    "modality_distribution": {"text": 0.4, "image": 0.3, "video": 0.15, "audio": 0.15},
}

# Recent observations buffer
_observations: list[dict] = []
_MAX_OBSERVATIONS = 500


@dataclass
class DriftAlert:
    metric: str
    baseline_value: float
    current_value: float
    deviation: float
    severity: str  # LOW, MEDIUM, HIGH
    recommendation: str

    def to_dict(self):
        return asdict(self)


@dataclass
class DriftReport:
    status: str  # NORMAL, POSSIBLE_DRIFT, DRIFT_DETECTED
    alerts: list[dict] = field(default_factory=list)
    observations_count: int = 0

    def to_dict(self):
        return asdict(self)


def record_observation(
    confidence: float,
    label: str,
    modality: str,
    risk_score: float | None = None,
):
    """Record a prediction observation for drift monitoring."""
    _observations.append({
        "confidence": confidence,
        "label": label,
        "modality": modality,
        "risk_score": risk_score,
    })
    if len(_observations) > _MAX_OBSERVATIONS:
        _observations.pop(0)


def detect_drift() -> dict:
    """Analyze recent observations for distribution drift."""
    if len(_observations) < 10:
        return DriftReport(status="NORMAL", observations_count=len(_observations)).to_dict()

    alerts = []
    recent = _observations[-200:]  # Last 200 observations

    # 1. Confidence drift
    confidences = [o["confidence"] for o in recent]
    mean_c = sum(confidences) / len(confidences)
    baseline_mean = _baseline["confidence_distribution"]["mean"]
    deviation = abs(mean_c - baseline_mean)
    if deviation > 0.15:
        alerts.append(DriftAlert(
            metric="confidence_distribution",
            baseline_value=baseline_mean,
            current_value=round(mean_c, 3),
            deviation=round(deviation, 3),
            severity="HIGH" if deviation > 0.25 else "MEDIUM",
            recommendation="Evaluate model performance on recent data",
        ).to_dict())

    # 2. Prediction distribution drift
    labels = Counter(o["label"] for o in recent)
    total = len(recent)
    for label, expected_pct in _baseline["prediction_distribution"].items():
        actual_pct = labels.get(label, 0) / total
        drift = abs(actual_pct - expected_pct)
        if drift > 0.15:
            alerts.append(DriftAlert(
                metric=f"prediction_distribution_{label}",
                baseline_value=expected_pct,
                current_value=round(actual_pct, 3),
                deviation=round(drift, 3),
                severity="HIGH" if drift > 0.25 else "MEDIUM",
                recommendation=f"Review {label} prediction rate — possible distribution shift",
            ).to_dict())

    # 3. Modality distribution drift
    modalities = Counter(o["modality"] for o in recent)
    for mod, expected_pct in _baseline["modality_distribution"].items():
        actual_pct = modalities.get(mod, 0) / total
        drift = abs(actual_pct - expected_pct)
        if drift > 0.15:
            alerts.append(DriftAlert(
                metric=f"modality_distribution_{mod}",
                baseline_value=expected_pct,
                current_value=round(actual_pct, 3),
                deviation=round(drift, 3),
                severity="LOW",
                recommendation=f"Input modality distribution for {mod} has shifted",
            ).to_dict())

    status = "NORMAL"
    if any(a["severity"] == "HIGH" for a in alerts):
        status = "DRIFT_DETECTED"
    elif alerts:
        status = "POSSIBLE_DRIFT"

    if alerts:
        logger.warning("Drift detection: %s with %d alerts", status, len(alerts))

    return DriftReport(
        status=status,
        alerts=alerts,
        observations_count=len(_observations),
    ).to_dict()
