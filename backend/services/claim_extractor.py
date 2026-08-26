"""Claim Extraction — splits text into individual claims. Stdlib only, no NLP dependency."""

import re


def extract_claims(text: str) -> list[dict]:
    """Split text into individual factual claims."""
    if not text or not text.strip():
        return []

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    claims = []
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 10:  # skip fragments
            continue
        # Simple importance heuristic: longer, more specific sentences score higher
        importance = min(1.0, len(sent) / 200)
        claims.append({"id": f"C{i+1}", "text": sent, "importance": round(importance, 2)})

    return claims
