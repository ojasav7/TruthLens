"""Evidence Explanation Engine — translates technical signals into human-readable explanations."""


def generate_explanation(investigation: dict, contradiction: dict | None = None) -> dict:
    """Generate a human-readable explanation from investigation data."""
    reasons = []
    unknowns = []

    # Analyze evidence
    for ev in investigation.get("evidence", []):
        if ev.get("category") == "SUPPORTING" and ev.get("score", 0) > 0.7:
            reasons.append({
                "text": f"{ev['type'].replace('_', ' ').title()}: {ev['description']}",
                "impact": ev.get("impact", "MEDIUM"),
            })

    # Analyze contradictions
    if contradiction and contradiction.get("status") == "inconsistent":
        for sig in contradiction.get("signals", []):
            reasons.append({
                "text": f"Cross-modal conflict: {sig.get('description', 'Modalities disagree')}",
                "impact": "HIGH",
            })

    # Check for missing evidence
    available = {ev.get("source_module") for ev in investigation.get("evidence", [])}
    for modality in ["text", "image", "video", "audio"]:
        if modality not in available:
            unknowns.append(f"{modality} analysis not available")

    # Classify
    risk_score = investigation.get("risk_score", 0) or 0
    if risk_score >= 70:
        category = "WHY_FLAGGED"
        summary = "The available evidence indicates elevated manipulation risk."
    elif risk_score >= 30:
        category = "WHAT_REQUIRES_REVIEW"
        summary = "The evidence is mixed. The system recommends human review."
    else:
        category = "WHY_NOT_FLAGGED"
        summary = "No significant manipulation signals detected."

    return {
        "category": category,
        "summary": summary,
        "primary_reasons": reasons[:5],  # top 5
        "unknowns": unknowns,
        "evidence_strength": investigation.get("strength", 0),
        "evidence_agreement": investigation.get("agreement", 0),
    }
