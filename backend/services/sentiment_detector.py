"""Sentiment Manipulation Detection — detect emotional manipulation tactics in text.

Identifies:
- Fear-mongering language
- Urgency/clickbait patterns
- Appeal to authority without evidence
- Emotional loaded language
- Logical fallacies (ad hominem, straw man, false dilemma)
- Missing attribution
"""

import re

# Manipulation tactic patterns
TACTICS = {
    "fear_mongering": {
        "patterns": [
            r"\bdanger(?:ous|ous)?\b", r"\bthreat\b", r"\bcatastroph",
            r"\bcrisis\b", r"\bemergency\b", r"\bwarning\b", r"\balert\b",
            r"\bdestroy\b", r"\bruin\b", r"\bcollapse\b", r"\bend of\b",
            r"\bterrifying\b", r"\bshocking\b", r"\bhorrible\b",
        ],
        "description": "Fear-mongering language designed to provoke anxiety",
        "severity": "high",
    },
    "urgency_clickbait": {
        "patterns": [
            r"you won.t believe", r"what happens next", r"click here",
            r"act now", r"limited time", r"hurry", r"before it.s too late",
            r"breaking:", r"just in:", r"exclusive:", r"shocking truth",
            r"they don.t want you to know", r"secret they re hiding",
            r"doctors hate", r"one weird trick",
        ],
        "description": "Urgency and clickbait tactics to bypass critical thinking",
        "severity": "medium",
    },
    "false_authority": {
        "patterns": [
            r"\bscientists say\b", r"\bexperts say\b", r"\bstudies show\b",
            r"\bresearch proves\b", r"\bdoctors say\b", r"\bgovernment\b",
            r"\baccording to experts\b", r"\bproven fact\b",
        ],
        "description": "Appeal to authority without specific citation",
        "severity": "medium",
    },
    "emotional_load": {
        "patterns": [
            r"\bshame(?:ful)?\b", r"\bdisgrace\b", r"\bcorrupt\b",
            r"\bevil\b", r"\btraitor\b", r"\bpatriot\b", r"\bhero\b",
            r"\bdevastat\b", r"\bhorrif\b", r"\bout rage\b", r"\bfurious\b",
            r"\bdisgusting\b", r"\babominable\b",
        ],
        "description": "Emotionally loaded language designed to bypass rational analysis",
        "severity": "low",
    },
    "logical_fallacy": {
        "patterns": [
            r"(?:all|every|always|never|none)\s+\w+\s+(?:are|is|do|does)",
            r"either\s+.+\s+or\s+.+",  # false dilemma
            r"if you re not with us",    # false dilemma
            r"(?:stupid|idiot|moron|sheep|brainwash)",  # ad hominem
        ],
        "description": "Logical fallacies used to manipulate reasoning",
        "severity": "medium",
    },
    "conspiracy_language": {
        "patterns": [
            r"\bcover.?up\b", r"\bconspiracy\b", r"\bthey re hiding\b",
            r"\bmainstream media\b", r"\bdeep state\b", r"\bshadow\b",
            r"\bhidden agenda\b", r"\bwake up\b", r"\bsheeple\b",
            r"\bpropaganda\b", r"\bcensored\b", r"\bsuppressed\b",
        ],
        "description": "Conspiracy-oriented language patterns",
        "severity": "high",
    },
    "missing_attribution": {
        "patterns": [
            r"(?:a|one) (?:study|report|survey|poll) (?:found|showed|revealed)",
            r"sources say\b", r"insiders claim\b",
            r"it has been reported\b", r"rumor has it\b",
        ],
        "description": "Claims without specific source attribution",
        "severity": "low",
    },
}


def detect_manipulation(text: str) -> dict:
    """
    Analyze text for emotional manipulation tactics.

    Returns:
        {
            "manipulation_score": float (0-100),
            "tactics_found": list[dict],
            "tactic_count": int,
            "severity": str,
            "explanation": str,
        }
    """
    if not text or not text.strip():
        return {
            "manipulation_score": 0.0,
            "tactics_found": [],
            "tactic_count": 0,
            "severity": "none",
            "explanation": "Empty text",
        }

    text_lower = text.lower()
    tactics_found = []

    for tactic_name, config in TACTICS.items():
        matches = []
        for pattern in config["patterns"]:
            found = re.findall(pattern, text_lower)
            matches.extend(found)

        if matches:
            tactics_found.append({
                "tactic": tactic_name,
                "description": config["description"],
                "severity": config["severity"],
                "match_count": len(matches),
                "samples": matches[:3],
            })

    # Score calculation
    score = 0
    severity_weights = {"high": 20, "medium": 12, "low": 5}
    for t in tactics_found:
        score += severity_weights.get(t["severity"], 5) * min(t["match_count"], 3)
    score = min(100, score)

    # Overall severity
    severities = [t["severity"] for t in tactics_found]
    if "high" in severities:
        overall_severity = "high"
    elif "medium" in severities:
        overall_severity = "medium"
    elif tactics_found:
        overall_severity = "low"
    else:
        overall_severity = "none"

    # Explanation
    if tactics_found:
        tactic_names = [t["tactic"].replace("_", " ") for t in tactics_found]
        explanation = f"Detected {len(tactics_found)} manipulation tactic(s): {', '.join(tactic_names)}"
    else:
        explanation = "No significant manipulation tactics detected"

    return {
        "manipulation_score": round(score, 2),
        "tactics_found": tactics_found,
        "tactic_count": len(tactics_found),
        "severity": overall_severity,
        "explanation": explanation,
    }


def text_health_report(text: str) -> dict:
    """Generate a comprehensive text health report combining all text analysis."""
    from backend.services.claim_extractor import extract_claims
    from backend.services.ai_text_detector import detect_ai_text

    manipulation = detect_manipulation(text)
    ai_detection = detect_ai_text(text)
    claims = extract_claims(text)

    # Overall trust score (100 = fully trustworthy, 0 = highly suspect)
    trust_score = 100.0
    trust_score -= manipulation["manipulation_score"] * 0.4
    trust_score -= ai_detection["confidence"] * 30 if ai_detection["is_ai_generated"] else 0
    trust_score -= len(claims) * 0  # claims count doesn't affect trust
    trust_score = max(0, min(100, trust_score))

    if trust_score >= 80:
        health = "HEALTHY"
    elif trust_score >= 50:
        health = "SUSPICIOUS"
    else:
        health = "UNTRUSTWORTHY"

    return {
        "trust_score": round(trust_score, 2),
        "health": health,
        "manipulation": manipulation,
        "ai_detection": ai_detection,
        "claim_count": len(claims),
        "summary": f"Trust score: {trust_score:.0f}/100 ({health}). "
                   f"{manipulation['tactic_count']} manipulation tactic(s). "
                   f"{'AI-generated' if ai_detection['is_ai_generated'] else 'Human-written'}."
    }
