"""Claim Extraction — extracts claims from text and matches to fact-check DB."""

import re

FACT_CHECK_DB = {
    "climate change": {"verdict": "supported", "sources": ["NASA", "NOAA"], "confidence": 0.95},
    "vaccine": {"verdict": "supported", "sources": ["WHO", "CDC"], "confidence": 0.92},
    "5g causes covid": {"verdict": "refuted", "sources": ["WHO", "FCC"], "confidence": 0.98},
    "earth is flat": {"verdict": "refuted", "sources": ["NASA", "ESA"], "confidence": 0.99},
}

CLAIM_PATTERNS = [
    r"(?:according to|research shows|studies indicate|experts say)",
    r"(?:definitely|certainly|absolutely|100%|proven|confirmed)",
    r"(?:causes?|leads to|results in|is responsible for)",
]


def extract_claims(text: str) -> dict:
    claims = []
    for sentence in re.split(r'[.!?]+', text):
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        if any(re.search(p, sentence, re.IGNORECASE) for p in CLAIM_PATTERNS):
            claims.append(_analyze_claim(sentence))

    verified = sum(1 for c in claims if c["evidence"])
    contradicted = sum(1 for c in claims if c["contradictions"])
    return {
        "claims": claims,
        "total_claims": len(claims),
        "verified_claims": verified,
        "contradicted_claims": contradicted,
        "confidence": sum(c["confidence"] for c in claims) / max(len(claims), 1),
    }


def match_evidence(claim: str) -> dict:
    claim_lower = claim.lower()
    for keyword, evidence in FACT_CHECK_DB.items():
        if keyword in claim_lower:
            return {"claim": claim, "matched": True, "evidence": evidence}
    return {"claim": claim, "matched": False, "evidence": None}


def _analyze_claim(sentence: str) -> dict:
    sentence_lower = sentence.lower()
    evidence, contradictions = [], []
    for keyword, info in FACT_CHECK_DB.items():
        if keyword in sentence_lower:
            (evidence if info["verdict"] == "supported" else contradictions).append(info)

    confidence = max((e["confidence"] for e in evidence + contradictions), default=0.3)
    return {
        "text": sentence,
        "confidence": confidence,
        "evidence": evidence,
        "contradictions": contradictions,
    }
