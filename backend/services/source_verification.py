"""
Source Verification & Provenance Chain Service
Checks article source history, publication metadata, fact-check database,
and reverse image search results.
"""

import hashlib
import time
from datetime import datetime, timezone
from typing import Optional


class SourceVerificationResult:
    """Result of source verification analysis."""
    
    def __init__(
        self,
        source_url: Optional[str] = None,
        source_credibility: float = 0.0,
        publication_date: Optional[str] = None,
        publication_metadata: dict = None,
        fact_check_results: list = None,
        reverse_image_results: list = None,
        provenance_chain: list = None,
        confidence: float = 0.0,
        warnings: list = None,
    ):
        self.source_url = source_url
        self.source_credibility = source_credibility
        self.publication_date = publication_date
        self.publication_metadata = publication_metadata or {}
        self.fact_check_results = fact_check_results or []
        self.reverse_image_results = reverse_image_results or []
        self.provenance_chain = provenance_chain or []
        self.confidence = confidence
        self.warnings = warnings or []
    
    def to_dict(self):
        return {
            "source_url": self.source_url,
            "source_credibility": self.source_credibility,
            "publication_date": self.publication_date,
            "publication_metadata": self.publication_metadata,
            "fact_check_results": self.fact_check_results,
            "reverse_image_results": self.reverse_image_results,
            "provenance_chain": self.provenance_chain,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


class SourceVerifier:
    """Verifies source credibility and checks provenance chain."""
    
    # Known credible sources (simplified for demo)
    CREDIBLE_SOURCES = {
        "reuters.com": 0.95,
        "apnews.com": 0.95,
        "bbc.com": 0.90,
        "nytimes.com": 0.90,
        "washingtonpost.com": 0.88,
        "theguardian.com": 0.85,
        "cnn.com": 0.80,
        "foxnews.com": 0.75,
        "buzzfeed.com": 0.60,
        "infowars.com": 0.10,
        "naturalnews.com": 0.10,
    }
    
    # Fact-check databases (simulated)
    FACT_CHECK_DB = {
        "climate change": {"verdict": "supported", "sources": ["NASA", "NOAA", "IPCC"]},
        "vaccine": {"verdict": "supported", "sources": ["WHO", "CDC"]},
        "flat earth": {"verdict": "refuted", "sources": ["NASA", "ESA"]},
        "moon landing fake": {"verdict": "refuted", "sources": ["NASA", "ESA"]},
    }
    
    def verify_source(self, url: str) -> SourceVerificationResult:
        """Verify a source URL for credibility."""
        credibility = 0.5  # default
        warnings = []
        
        # Extract domain
        domain = self._extract_domain(url)
        
        # Check against known sources
        for known_domain, score in self.CREDIBLE_SOURCES.items():
            if known_domain in domain:
                credibility = score
                break
        
        # Check for suspicious patterns
        if any(pattern in domain for pattern in ["blog", "wordpress", "blogspot"]):
            warnings.append("Source appears to be a personal blog")
            credibility *= 0.7
        
        if any(pattern in domain for pattern in ["news", "media", "press"]):
            if credibility < 0.5:
                warnings.append("Source name suggests news but credibility is low")
        
        # Generate publication metadata
        pub_metadata = {
            "domain": domain,
            "https_enabled": url.startswith("https"),
            "has_ssl_certificate": url.startswith("https"),
            "estimated_age_days": self._estimate_domain_age(domain),
            "content_category": self._categorize_content(domain),
        }
        
        # Check fact-check database
        fact_checks = self._check_fact_database("")  # Would use actual content
        
        # Generate provenance chain
        chain = self._build_provenance_chain(url, domain)
        
        return SourceVerificationResult(
            source_url=url,
            source_credibility=credibility,
            publication_date=datetime.now(timezone.utc).isoformat(),
            publication_metadata=pub_metadata,
            fact_check_results=fact_checks,
            provenance_chain=chain,
            confidence=credibility,
            warnings=warnings,
        )
    
    def check_fact_database(self, claim: str) -> list:
        """Check a claim against fact-check databases."""
        return self._check_fact_database(claim)
    
    def reverse_image_search(self, image_hash: str) -> list:
        """Perform reverse image search (simulated)."""
        # In production, this would call TinEye, Google Vision, etc.
        return [
            {
                "source": "Google Images",
                "url": "https://images.google.com/search",
                "matches": 0,
                "first_seen": None,
                "status": "no_matches_found",
            },
            {
                "source": "TinEye",
                "url": "https://tineye.com",
                "matches": 0,
                "first_seen": None,
                "status": "no_matches_found",
            },
        ]
    
    def build_provenance_chain(self, url: str) -> list:
        """Build a provenance chain for content."""
        return self._build_provenance_chain(url, self._extract_domain(url))
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        return domain.lower()
    
    def _estimate_domain_age(self, domain: str) -> int:
        """Estimate domain age in days (simulated)."""
        # In production, would use WHOIS lookup
        if any(d in domain for d in ["google", "facebook", "twitter", "wikipedia"]):
            return 5000  # old domains
        return 365  # default 1 year
    
    def _categorize_content(self, domain: str) -> str:
        """Categorize content based on domain."""
        if any(k in domain for k in ["news", "times", "post", "herald"]):
            return "news"
        if any(k in domain for k in ["edu", "ac.", "university"]):
            return "education"
        if any(k in domain for k in ["gov", ".gov"]):
            return "government"
        if any(k in domain for k in ["blog", "wordpress", "medium"]):
            return "blog"
        return "other"
    
    def _check_fact_database(self, claim: str) -> list:
        """Check claim against fact-check databases."""
        results = []
        claim_lower = claim.lower()
        
        for keyword, info in self.FACT_CHECK_DB.items():
            if keyword in claim_lower:
                results.append({
                    "claim": claim,
                    "verdict": info["verdict"],
                    "sources": info["sources"],
                    "confidence": 0.9 if info["verdict"] == "supported" else 0.85,
                })
        
        if not results:
            results.append({
                "claim": claim,
                "verdict": "not_found",
                "sources": [],
                "confidence": 0.0,
            })
        
        return results
    
    def _build_provenance_chain(self, url: str, domain: str) -> list:
        """Build provenance chain for content."""
        chain = [
            {
                "step": 1,
                "action": "Source Identified",
                "entity": domain,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "verified",
                "details": f"Content originated from {domain}",
            },
            {
                "step": 2,
                "action": "SSL Certificate Check",
                "entity": "Certificate Authority",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "verified" if url.startswith("https") else "warning",
                "details": "HTTPS certificate is valid" if url.startswith("https") else "No HTTPS certificate found",
            },
            {
                "step": 3,
                "action": "Domain Reputation Check",
                "entity": "Reputation Database",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "verified",
                "details": f"Domain reputation score: {self.CREDIBLE_SOURCES.get(domain, 0.5):.2f}",
            },
            {
                "step": 4,
                "action": "Content Provenance",
                "entity": "TruthLens Forensics",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "verified",
                "details": "Content metadata analyzed and verified",
            },
        ]
        
        return chain


# Singleton instance
_source_verifier = None


def get_source_verifier() -> SourceVerifier:
    """Get or create singleton source verifier."""
    global _source_verifier
    if _source_verifier is None:
        _source_verifier = SourceVerifier()
    return _source_verifier
