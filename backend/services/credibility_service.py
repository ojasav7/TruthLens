"""Source credibility scoring — check URLs against known low-credibility domains."""

import re
from urllib.parse import urlparse

# ponytail: static list, swap with API when needed
LOW_CREDIBILITY_DOMAINS = {
    # Fake news / satire mislabeled as news
    "infowars.com", "naturalnews.com", "beforeitsnews.com", "worldnewsdailyreport.com",
    "dailywire.com", "breitbart.com", "gatewaypundit.com", "thegatewaypundit.com",
    "projectveritas.com", "dailyCaller.com", "westernjournal.com",
    # Clickbait farms
    "boredpanda.com", "viralthread.com", "forall.com", "didyouknowfacts.com",
    # State propaganda (various)
    "rt.com", "sputniknews.com", "presstv.ir", "globaltimes.cn",
    # Conspiracy
    "beforeitsnews.com", "disclose.tv", "nworeport.me",
    # Hyper-partisan
    "occupycorporatism.com", "truth11.com", "constitution.com",
}

HIGH_CREDIBILITY_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com",
    "washingtonpost.com", "theguardian.com", "economist.com", "nature.com",
    "science.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
    "who.int", "cdc.gov", "nih.gov", "un.org", "worldbank.org",
}


def check_url(url: str) -> dict:
    """
    Check a URL's domain against known credibility lists.

    Args:
        url: URL string (with or without protocol)

    Returns:
        {
            "domain": str,
            "credibility": "low" | "unknown" | "high",
            "risk_score": float (0-1, higher = less credible),
            "signals": list[str]
        }
    """
    if not url or not isinstance(url, str):
        return {"domain": "", "credibility": "unknown", "risk_score": 0.5, "signals": ["No URL provided"]}

    # Extract domain
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().removeprefix("www.")
    except Exception:
        return {"domain": url, "credibility": "unknown", "risk_score": 0.5, "signals": ["Could not parse URL"]}

    signals = []

    if domain in LOW_CREDIBILITY_DOMAINS:
        signals.append(f"Domain '{domain}' is on low-credibility list")
        return {"domain": domain, "credibility": "low", "risk_score": 0.9, "signals": signals}

    if domain in HIGH_CREDIBILITY_DOMAINS:
        signals.append(f"Domain '{domain}' is a recognized credible source")
        return {"domain": domain, "credibility": "high", "risk_score": 0.1, "signals": signals}

    # Heuristic checks for unknown domains
    risk = 0.5

    # Check for suspicious patterns
    if re.search(r"\d{4,}", domain):
        signals.append("Domain contains many numbers — possible fake")
        risk += 0.15

    if domain.count("-") > 3:
        signals.append("Excessive hyphens in domain — possible fake")
        risk += 0.1

    # Check TLD
    suspicious_tlds = {".xyz", ".top", ".buzz", ".click", ".link", ".info", ".tk"}
    for tld in suspicious_tlds:
        if domain.endswith(tld):
            signals.append(f"Suspicious TLD ({tld})")
            risk += 0.15
            break

    credibility = "low" if risk >= 0.7 else "high" if risk <= 0.3 else "unknown"

    if not signals:
        signals.append("Domain not in known lists — credibility unknown")

    return {"domain": domain, "credibility": credibility, "risk_score": round(min(risk, 1.0), 2), "signals": signals}
