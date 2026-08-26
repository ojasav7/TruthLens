"""Explain Like I'm Human — maps technical signals to plain English."""

TECHNICAL_TO_HUMAN = {
    "facial_inconsistency": "The face in this content doesn't look entirely natural",
    "face_swap_detected": "This appears to be a face-swap — one person's face placed on another body",
    "lip_sync_anomaly": "The mouth movements don't consistently match the spoken words",
    "voice_clone_detected": "The voice may not belong to the person speaking",
    "audio_visual_mismatch": "The audio and video don't seem to come from the same source",
    "text_fake": "The text uses patterns commonly seen in misinformation",
    "text_real": "The text reads like typical news content",
    "image_suspicious": "This image shows signs of digital manipulation",
    "image_authentic": "This image appears to be an original photograph",
    "metadata_missing": "Important file information is missing — this can happen with edited content",
    "metadata_edited": "The file metadata suggests this content was edited with software",
    "source_untrusted": "This source is not among widely recognized credible outlets",
    "source_trusted": "This source is a recognized credible outlet",
    "claim_unverified": "This claim could not be matched against known fact-checks",
}


def to_human(technical_description: str, category: str = "WHY_FLAGGED") -> str:
    """Convert a technical description to human-friendly language."""
    # Try exact match first
    desc_lower = technical_description.lower()
    for key, human in TECHNICAL_TO_HUMAN.items():
        if key in desc_lower:
            return human

    # Category-based fallback
    if category == "WHY_FLAGGED":
        return f"This content raised concerns: {technical_description}"
    elif category == "WHY_NOT_FLAGGED":
        return f"No significant issues detected: {technical_description}"
    elif category == "WHAT_IS_UNKNOWN":
        return f"We couldn't fully analyze this: {technical_description}"
    elif category == "WHAT_REQUIRES_REVIEW":
        return f"This needs a closer look: {technical_description}"

    return technical_description


def explain_investigation(investigation: dict) -> dict:
    """Generate a full human-mode explanation."""
    explanation = investigation.get("explanation", {})
    summary = explanation.get("summary", "No analysis available.")
    reasons = explanation.get("primary_reasons", [])
    unknowns = explanation.get("unknowns", [])

    human_reasons = []
    for r in reasons[:5]:
        text = r.get("text", "") if isinstance(r, dict) else str(r)
        human_reasons.append(to_human(text))

    human_unknowns = [to_human(u, "WHAT_IS_UNKNOWN") for u in unknowns[:5]]

    return {
        "plain_english_summary": summary,
        "plain_english_reasons": human_reasons,
        "plain_english_unknowns": human_unknowns,
        "technical_available": True,
    }
