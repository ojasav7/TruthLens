"""'Do Not Overclaim' Validator.

Before displaying or exporting a final assessment, check for
unsupported certainty language.
"""

import re
import logging

logger = logging.getLogger("truthlens.overclaim")

# Patterns that imply unsupported certainty
OVERCLAIM_PATTERNS = [
    (r"\bdefinitely\s+(fake|authentic|real|true|false)\b", "unsupported_certainty"),
    (r"\bproves?\b", "unsupported_proof"),
    (r"\bundeniably\b", "unsupported_certainty"),
    (r"\bwithout\s+doubt\b", "unsupported_certainty"),
    (r"\b100%\s+(sure|certain|fake|real)\b", "unsupported_certainty"),
    (r"\bthis\s+(is|proves)\s+(definitely|certainly|absolutely)\b", "unsupported_certainty"),
    (r"\babsolutely\s+(fake|real|authentic|manipulated)\b", "unsupported_certainty"),
]

# Preferred hedging replacements
PREFERRED_LANGUAGE = {
    "definitely fake": "evidence indicates manipulation",
    "definitely authentic": "no significant manipulation signals detected",
    "definitely real": "analysis indicates authenticity",
    "proves": "suggests",
    "proven": "indicated by available evidence",
}


def validate_overclaims(text: str) -> dict:
    """Check text for unsupported certainty language."""
    violations = []
    for pattern, category in OVERCLAIM_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            violations.append({
                "text": match.group(),
                "category": category,
                "position": match.span(),
                "suggestion": PREFERRED_LANGUAGE.get(match.group().lower(), "consider hedging"),
            })

    return {
        "has_overclaims": len(violations) > 0,
        "violations": violations,
        "count": len(violations),
    }


def suggest_rewrites(text: str) -> str:
    """Suggest rewrites for overclaiming language."""
    result = text
    for original, preferred in PREFERRED_LANGUAGE.items():
        result = re.sub(re.escape(original), preferred, result, flags=re.IGNORECASE)
    return result


def validate_assessment_language(verdict: str, explanation: str, risk_score: float) -> dict:
    """Validate that the assessment language is appropriate."""
    overclaims = validate_overclaims(explanation)
    hedged = suggest_rewrites(explanation)

    # Check verdict/score alignment
    verdict_appropriate = True
    if risk_score < 30 and "high risk" in verdict.lower():
        verdict_appropriate = False
    if risk_score > 70 and "low" in verdict.lower() and "risk" in verdict.lower():
        verdict_appropriate = False

    return {
        "language_valid": not overclaims["has_overclaims"] and verdict_appropriate,
        "overclaim_check": overclaims,
        "hedged_explanation": hedged if overclaims["has_overclaims"] else None,
        "verdict_appropriate": verdict_appropriate,
        "recommendation": (
            "Assessment language is appropriate."
            if not overclaims["has_overclaims"] and verdict_appropriate
            else "Consider using hedged language: 'evidence indicates...' rather than definitive statements."
        ),
    }
