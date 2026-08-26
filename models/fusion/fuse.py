"""
Fusion Layer — Phase 5
Combines predictions from multiple modalities into a single threat score and verdict.
Includes cross-modal consistency checks and confidence calibration.
"""

DEFAULT_WEIGHTS = {
    "text": 0.25,
    "image": 0.25,
    "video": 0.35,
    "audio": 0.15,
}


def _calibrate_confidence(conf: float, modality: str) -> float:
    """Platt-style calibration — push extreme confidences toward center."""
    # ponytail: naive calibration, replace with learned Platt scaling when real data available
    calibrated = 0.5 + (conf - 0.5) * 0.85  # shrink toward 50% by 15%
    return round(min(max(calibrated, 0.0), 1.0), 4)


def fuse(scores: dict, weights: dict | None = None) -> dict:
    """
    Fuse modality scores into a single threat score.

    Args:
        scores: dict of modality predictions, e.g.
            {"text": {"label": "fake", "confidence": 0.81}, "image": None, ...}
        weights: optional override for default weights.

    Returns:
        {"threat_score": 0-100, "verdict": "Low"|"Review Needed"|"High Risk", "breakdown": dict}
    """
    w = weights or DEFAULT_WEIGHTS.copy()

    active = {mod: res for mod, res in scores.items() if res is not None and mod in w}

    if not active:
        return {"threat_score": 0.0, "verdict": "Low", "breakdown": scores}

    # Renormalize weights over active modalities
    total_w = sum(w[mod] for mod in active)
    norm_weights = {mod: w[mod] / total_w for mod in active}

    # Compute per-modality threat contributions with calibration
    threat = 0.0
    breakdown = {}
    fake_count = 0
    real_count = 0

    for mod, result in active.items():
        label = result.get("label", "real")
        raw_conf = result.get("confidence", 0.0)
        conf = _calibrate_confidence(raw_conf, mod)

        if label in ("fake", "cloned"):
            mod_threat = conf * 100
            fake_count += 1
        else:
            mod_threat = (1 - conf) * 100
            real_count += 1

        threat += norm_weights[mod] * mod_threat
        breakdown[mod] = {
            "label": label,
            "confidence": raw_conf,
            "calibrated_confidence": conf,
            "weight": round(norm_weights[mod], 4),
            "threat_contribution": round(mod_threat, 2),
        }

    # Cross-modal consistency: boost threat when modalities disagree
    n_active = len(active)
    if n_active > 1:
        total_modalities = fake_count + real_count
        agreement_ratio = max(fake_count, real_count) / total_modalities
        # agreement_ratio: 1.0 = full agreement, 0.5 = perfect disagreement
        # If modalities disagree, add up to 10 points to threat
        disagreement_boost = (1 - agreement_ratio) * 15
        threat += disagreement_boost

    threat_score = round(min(max(threat, 0), 100), 2)
    verdict = "Low" if threat_score <= 30 else "Review Needed" if threat_score <= 70 else "High Risk"

    # Consistency summary
    consistency = "unanimous" if n_active <= 1 or fake_count == 0 or real_count == 0 else "mixed"

    return {
        "threat_score": threat_score,
        "verdict": verdict,
        "consistency": consistency,
        "breakdown": {**scores, **breakdown},
    }
