"""Evidence Explanation Engine — translates technical signals into human-readable explanations."""


def verify_explanation(explanation: str = "", evidence_count: int = 0, has_provenance: bool = False, has_fact_check: bool = False, has_model_signal: bool = False, has_evidence: bool = False) -> dict:
    """Verify explanation is supported by evidence."""
    issues = []
    if not explanation:
        issues.append("No explanation provided")
    if not has_model_signal:
        issues.append("No model signal to support explanation")
    if not has_evidence and evidence_count == 0:
        issues.append("No evidence to support explanation")
    if not has_provenance:
        issues.append("Provenance not verified")
    is_supported = len(issues) == 0
    return {
        "is_supported": is_supported,
        "supported": is_supported,
        "warning": issues[0] if issues else None,
        "issues": issues,
        "evidence_count": evidence_count,
    }


def explain_investigation(investigation: dict) -> dict:
    """Wrapper for backward compat. Calls generate_explanation."""
    return generate_explanation(investigation)


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
        "plain_english_summary": summary,  # compat alias
        "primary_reasons": reasons[:5],
        "plain_english_reasons": [r["text"] for r in reasons[:5]],
        "unknowns": unknowns,
        "evidence_strength": investigation.get("strength", 0),
        "evidence_agreement": investigation.get("agreement", 0),
        "technical_available": len(investigation.get("evidence", [])) > 0,
    }
