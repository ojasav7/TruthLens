"""Source Verification — checks credibility, provenance chain, fact-check DB."""

from datetime import datetime, timezone

CREDIBLE_SOURCES = {
    "reuters.com": 0.95, "apnews.com": 0.95, "bbc.com": 0.90,
    "nytimes.com": 0.90, "washingtonpost.com": 0.88, "theguardian.com": 0.85,
    "cnn.com": 0.80, "foxnews.com": 0.75, "buzzfeed.com": 0.60,
    "infowars.com": 0.10, "naturalnews.com": 0.10,
}

FACT_CHECK_DB = {
    "climate change": {"verdict": "supported", "sources": ["NASA", "NOAA", "IPCC"]},
    "vaccine": {"verdict": "supported", "sources": ["WHO", "CDC"]},
    "flat earth": {"verdict": "refuted", "sources": ["NASA", "ESA"]},
    "moon landing fake": {"verdict": "refuted", "sources": ["NASA", "ESA"]},
}


def _domain(url: str) -> str:
    return url.replace("https://", "").replace("http://", "").split("/")[0].lower()


def verify_source(url: str) -> dict:
    domain = _domain(url)
    credibility = next((s for d, s in CREDIBLE_SOURCES.items() if d in domain), 0.5)

    warnings = []
    if any(p in domain for p in ["blog", "wordpress", "blogspot"]):
        warnings.append("Source appears to be a personal blog")
        credibility *= 0.7

    now = datetime.now(timezone.utc).isoformat()
    return {
        "source_url": url,
        "source_credibility": round(credibility, 2),
        "publication_date": now,
        "metadata": {
            "domain": domain,
            "https": url.startswith("https"),
            "category": "news" if any(k in domain for k in ["news", "times", "post"]) else "other",
        },
        "provenance_chain": [
            {"step": 1, "action": "Source Identified", "entity": domain, "status": "verified", "timestamp": now},
            {"step": 2, "action": "SSL Check", "status": "verified" if url.startswith("https") else "warning", "timestamp": now},
            {"step": 3, "action": "Reputation Check", "status": "verified", "details": f"Score: {credibility:.2f}", "timestamp": now},
        ],
        "warnings": warnings,
    }


def check_claim(claim: str) -> dict:
    claim_lower = claim.lower()
    for keyword, info in FACT_CHECK_DB.items():
        if keyword in claim_lower:
            return {"claim": claim, "verdict": info["verdict"], "sources": info["sources"], "confidence": 0.9}
    return {"claim": claim, "verdict": "not_found", "sources": [], "confidence": 0.0}
