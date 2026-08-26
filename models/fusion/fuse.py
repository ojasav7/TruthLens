"""
Fusion Layer — Phase 5
Combines predictions from multiple modalities into a single threat score and verdict.
"""

# Default weights per modality (sum to 1.0)
DEFAULT_WEIGHTS = {
    "text": 0.25,
    "image": 0.25,
    "video": 0.35,
    "audio": 0.15,
}




def fuse(
    scores: dict,
    weights: dict | None = None,
) -> dict:
    """
    Fuse modality scores into a single threat score.

    Args:
        scores: dict of modality predictions, e.g.
            {
                "text": {"label": "fake", "confidence": 0.81},
                "image": {"label": "real", "confidence": 0.60},
                "video": None,
                "audio": None,
            }
            Modalities with None or missing are excluded.

        weights: optional override for default weights.

    Returns:
        {
            "threat_score": float (0-100),
            "verdict": str ("Low"|"Review Needed"|"High Risk"),
            "breakdown": dict,
        }
    """
    w = weights or DEFAULT_WEIGHTS.copy()

    # Filter to only modalities that have results
    active = {}
    for mod, result in scores.items():
        if result is not None and mod in w:
            active[mod] = result

    if not active:
        return {
            "threat_score": 0.0,
            "verdict": "Low",
            "breakdown": scores,
        }

    # Renormalize weights to sum to 1 over active modalities only
    total_w = sum(w[mod] for mod in active)
    norm_weights = {mod: w[mod] / total_w for mod in active}

    # Convert each modality's confidence into a "fake threat" score:
    # - If label == "fake"/"cloned": threat contribution = confidence * 100
    # - If label == "real": threat contribution = (1 - confidence) * 100
    threat = 0.0
    breakdown = {}
    for mod, result in active.items():
        label = result.get("label", "real")
        conf = result.get("confidence", 0.0)

        if label in ("fake", "cloned"):
            mod_threat = conf * 100
        else:
            mod_threat = (1 - conf) * 100

        threat += norm_weights[mod] * mod_threat
        breakdown[mod] = {
            "label": label,
            "confidence": conf,
            "weight": round(norm_weights[mod], 4),
            "threat_contribution": round(mod_threat, 2),
        }

    threat_score = round(min(max(threat, 0), 100), 2)
    verdict = "Low" if threat_score <= 30 else "Review Needed" if threat_score <= 70 else "High Risk"

    return {
        "threat_score": threat_score,
        "verdict": verdict,
        "breakdown": {**scores, **breakdown},
    }
