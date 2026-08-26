"""Investigation Prioritization — auto-assigns priority based on risk + evidence signals."""


def calculate_priority(risk_score: float | None, evidence: list[dict] | None = None, consistency: str | None = None) -> str:
    """Determine case priority from risk score and evidence signals."""
    if risk_score is None:
        return "LOW"

    score = 0

    # Risk score contribution (0-4 points)
    if risk_score >= 80:
        score += 4
    elif risk_score >= 60:
        score += 3
    elif risk_score >= 40:
        score += 2
    elif risk_score >= 20:
        score += 1

    # Evidence disagreement (0-2 points)
    if consistency == "mixed":
        score += 2

    # Low evidence strength (0-1 point)
    if evidence and len(evidence) < 2:
        score += 1

    # Map score to priority
    if score >= 5:
        return "CRITICAL"
    elif score >= 3:
        return "HIGH"
    elif score >= 1:
        return "MEDIUM"
    return "LOW"
