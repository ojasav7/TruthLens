"""Claim Extraction — extracts claims from text using transformers zero-shot classification."""

import re

# NLP model disabled by default (loads slowly on CPU)
# Set USE_NLP_MODEL=1 to enable bart-large-mnli zero-shot classification
import os
_use_nlp = os.getenv("USE_NLP_MODEL", "0") == "1"
_classifier = None


def _get_classifier():
    global _classifier
    if _use_nlp and _classifier is None:
        from transformers import pipeline
        _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
    return _classifier

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

CANDIDATE_LABELS = ["factual claim", "opinion", "question", "statement of fact"]


def extract_claims(text: str) -> dict:
    claims = []
    for sentence in re.split(r'[.!?]+', text):
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue

        clf = _get_classifier()
        if clf:
            result = clf(sentence, CANDIDATE_LABELS)
            top_label = result["labels"][0]
            top_score = result["scores"][0]
            # Only extract if classified as a factual claim with decent confidence
            if top_label == "factual claim" and top_score > 0.5:
                claims.append(_analyze_claim(sentence, top_score))
        else:
            # Fallback: regex-based extraction
            if any(re.search(p, sentence, re.IGNORECASE) for p in CLAIM_PATTERNS):
                claims.append(_analyze_claim(sentence, 0.5))

    verified = sum(1 for c in claims if c["evidence"])
    contradicted = sum(1 for c in claims if c["contradictions"])
    return {
        "claims": claims,
        "total_claims": len(claims),
        "verified_claims": verified,
        "contradicted_claims": contradicted,
        "confidence": sum(c["confidence"] for c in claims) / max(len(claims), 1),
        "model_used": "bart-large-mnli" if _get_classifier() else "regex-fallback",
    }


def match_evidence(claim: str) -> dict:
    claim_lower = claim.lower()
    for keyword, evidence in FACT_CHECK_DB.items():
        if keyword in claim_lower:
            return {"claim": claim, "matched": True, "evidence": evidence}
    return {"claim": claim, "matched": False, "evidence": None}


def _analyze_claim(sentence: str, nlp_confidence: float) -> dict:
    sentence_lower = sentence.lower()
    evidence, contradictions = [], []
    for keyword, info in FACT_CHECK_DB.items():
        if keyword in sentence_lower:
            (evidence if info["verdict"] == "supported" else contradictions).append(info)

    # Blend NLP confidence with fact-check confidence
    if evidence or contradictions:
        fc_confidence = max((e["confidence"] for e in evidence + contradictions), default=0.5)
        confidence = (nlp_confidence + fc_confidence) / 2
    else:
        confidence = nlp_confidence * 0.5  # Uncorroborated claims get lower confidence

    return {
        "text": sentence,
        "confidence": round(confidence, 3),
        "evidence": evidence,
        "contradictions": contradictions,
    }
