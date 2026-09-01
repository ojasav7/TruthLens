"""Explainability — human-friendly summaries for model decisions."""


def explain(modality: str, prediction: dict) -> dict:
    label = prediction.get("label", "unknown")
    confidence = prediction.get("confidence", 0)
    signals = prediction.get("signals", {})

    summary = _summary(modality, label, confidence)
    indicators = _indicators(modality, label, signals)
    recommendations = _recommendations(label, confidence)

    return {
        "summary": summary,
        "indicators": indicators,
        "recommendations": recommendations,
        "modality": modality,
        "label": label,
        "confidence": confidence,
    }


def _summary(modality: str, label: str, confidence: float) -> str:
    mod = modality.capitalize()
    if label in ("fake", "cloned"):
        strength = "strongly" if confidence > 0.8 else "suggests" if confidence > 0.6 else "weakly"
        return f"The {mod} analysis {strength} indicates this content is not authentic."
    if label in ("real", "genuine"):
        strength = "strongly" if confidence > 0.8 else "suggests" if confidence > 0.6 else "weakly"
        return f"The {mod} analysis {strength} indicates this content is authentic."
    return f"The {mod} analysis was inconclusive."


def _indicators(modality: str, label: str, signals: dict) -> list:
    indicators = []
    checks = {
        "text": [("emotional_appeal", "High emotional appeal", 0.7),
                 ("fact_check_score", "Low fact-check alignment", 0.3),
                 ("source_credibility", "Low source credibility", 0.3)],
        "image": [("frequency_artifacts", "Frequency domain anomalies", 0.7),
                  ("compression_artifacts", "Compression inconsistencies", 0.6)],
        "audio": [("voice_clone_signs", "Voice cloning indicators", 0.7),
                  ("temporal_consistency", "Temporal inconsistencies", 0.3)],
        "video": [("lip_sync_accuracy", "Lip sync issues", 0.3),
                  ("face_tracking", "Facial feature anomalies", 0.4)],
    }
    for key, desc, threshold in checks.get(modality, []):
        val = signals.get(key, 0)
        if isinstance(val, (int, float)):
            is_critical = (val > threshold) != (key in ("fact_check_score", "source_credibility", "temporal_consistency", "lip_sync_accuracy"))
            if is_critical and abs(val) > threshold:
                indicators.append({"indicator": desc, "severity": "critical" if abs(val) > 0.7 else "warning"})
    return indicators


def _recommendations(label: str, confidence: float) -> list:
    recs = []
    if label in ("fake", "cloned"):
        if confidence > 0.8:
            recs.append({"action": "Do not share", "priority": "high"})
        elif confidence > 0.6:
            recs.append({"action": "Exercise caution", "priority": "medium"})
    elif label in ("real", "genuine"):
        recs.append({"action": "Content appears authentic", "priority": "low"})
    return recs
