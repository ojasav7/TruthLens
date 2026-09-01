"""
Claim Extraction & Evidence Matching Service
Extracts claims from text, matches them to known sources,
and compares media captions with actual content.
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Claim:
    """Represents an extracted claim."""
    text: str
    category: str
    confidence: float
    evidence: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    sources: list = field(default_factory=list)


@dataclass
class ClaimExtractionResult:
    """Result of claim extraction."""
    claims: list
    total_claims: int
    verified_claims: int
    contradicted_claims: int
    unknown_claims: int
    confidence: float
    contradictions: list = field(default_factory=list)


class ClaimExtractor:
    """Extracts and verifies claims from text."""
    
    # Claim patterns (simplified)
    CLAIM_PATTERNS = [
        r"(?:according to|research shows|studies indicate|experts say|scientists found)",
        r"(?:definitely|certainly|absolutely|100%|proven|confirmed)",
        r"(?:causes?|leads to|results in|is responsible for)",
        r"(?:will happen|going to|predict|forecast)",
    ]
    
    # Evidence database (simulated)
    EVIDENCE_DB = {
        "climate change": {
            "verdict": "supported",
            "confidence": 0.95,
            "sources": ["NASA Climate", "NOAA", "IPCC Reports"],
            "summary": "Overwhelming scientific consensus supports climate change",
        },
        "vaccine safety": {
            "verdict": "supported",
            "confidence": 0.92,
            "sources": ["WHO", "CDC", "Peer-reviewed studies"],
            "summary": "Extensive research confirms vaccine safety and efficacy",
        },
        "5g causes covid": {
            "verdict": "refuted",
            "confidence": 0.98,
            "sources": ["WHO", "FCC", "Scientific consensus"],
            "summary": "No evidence links 5G technology to COVID-19",
        },
        "earth is flat": {
            "verdict": "refuted",
            "confidence": 0.99,
            "sources": ["NASA", "ESA", "Scientific consensus"],
            "summary": "Overwhelming evidence confirms Earth is spherical",
        },
    }
    
    def extract_claims(self, text: str) -> ClaimExtractionResult:
        """Extract claims from text."""
        claims = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # Check if sentence matches claim patterns
            for pattern in self.CLAIM_PATTERNS:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claim = self._analyze_claim(sentence)
                    if claim:
                        claims.append(claim)
                    break
        
        # Calculate statistics
        total = len(claims)
        verified = sum(1 for c in claims if c.evidence and not c.contradictions)
        contradicted = sum(1 for c in claims if c.contradictions)
        unknown = total - verified - contradicted
        
        # Calculate overall confidence
        if total > 0:
            confidence = sum(c.confidence for c in claims) / total
        else:
            confidence = 0.5
        
        return ClaimExtractionResult(
            claims=[self._claim_to_dict(c) for c in claims],
            total_claims=total,
            verified_claims=verified,
            contradicted_claims=contradicted,
            unknown_claims=unknown,
            confidence=confidence,
            contradictions=[c.contradictions for c in claims if c.contradictions],
        )
    
    def match_evidence(self, claim_text: str) -> dict:
        """Match a claim to known evidence."""
        claim_lower = claim_text.lower()
        
        # Check against evidence database
        for keyword, evidence in self.EVIDENCE_DB.items():
            if keyword in claim_lower:
                return {
                    "claim": claim_text,
                    "matched": True,
                    "evidence": evidence,
                }
        
        return {
            "claim": claim_text,
            "matched": False,
            "evidence": None,
        }
    
    def compare_media_caption(self, caption: str, media_analysis: dict) -> dict:
        """Compare media caption with actual media content analysis."""
        # Extract key claims from caption
        caption_claims = self._extract_caption_claims(caption)
        
        # Compare with media analysis
        contradictions = []
        matches = []
        
        for claim in caption_claims:
            claim_lower = claim.lower()
            
            # Check if caption contradicts media analysis
            if media_analysis.get("label") == "fake":
                if any(word in claim_lower for word in ["real", "authentic", "genuine", "official"]):
                    contradictions.append({
                        "caption_claim": claim,
                        "media_finding": "Media appears manipulated",
                        "type": "contradiction",
                    })
            elif media_analysis.get("label") == "real":
                if any(word in claim_lower for word in ["fake", "manipulated", "altered", "edited"]):
                    contradictions.append({
                        "caption_claim": claim,
                        "media_finding": "Media appears authentic",
                        "type": "contradiction",
                    })
                else:
                    matches.append({
                        "caption_claim": claim,
                        "media_finding": "Media appears authentic",
                        "type": "match",
                    })
        
        return {
            "caption": caption,
            "caption_claims": caption_claims,
            "matches": matches,
            "contradictions": contradictions,
            "consistency_score": len(matches) / max(len(caption_claims), 1),
        }
    
    def _analyze_claim(self, sentence: str) -> Optional[Claim]:
        """Analyze a single claim."""
        sentence_lower = sentence.lower()
        
        # Determine category
        category = "general"
        if any(word in sentence_lower for word in ["research", "study", "scientist"]):
            category = "scientific"
        elif any(word in sentence_lower for word in ["health", "medical", "disease"]):
            category = "health"
        elif any(word in sentence_lower for word in ["political", "government", "election"]):
            category = "political"
        
        # Check evidence database
        evidence = []
        contradictions = []
        
        for keyword, info in self.EVIDENCE_DB.items():
            if keyword in sentence_lower:
                if info["verdict"] == "supported":
                    evidence.append(info)
                elif info["verdict"] == "refuted":
                    contradictions.append(info)
        
        # Calculate confidence
        if evidence:
            confidence = max(e["confidence"] for e in evidence)
        elif contradictions:
            confidence = max(c["confidence"] for c in contradictions)
        else:
            confidence = 0.3  # Low confidence for unverified claims
        
        return Claim(
            text=sentence,
            category=category,
            confidence=confidence,
            evidence=evidence,
            contradictions=contradictions,
            sources=[],
        )
    
    def _extract_caption_claims(self, caption: str) -> list:
        """Extract claims from a media caption."""
        claims = []
        
        # Split caption into phrases
        phrases = re.split(r'[,;.]', caption)
        
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) > 5:
                claims.append(phrase)
        
        return claims
    
    def _claim_to_dict(self, claim: Claim) -> dict:
        """Convert Claim to dictionary."""
        return {
            "text": claim.text,
            "category": claim.category,
            "confidence": claim.confidence,
            "evidence": claim.evidence,
            "contradictions": claim.contradictions,
            "sources": claim.sources,
        }


# Singleton instance
_claim_extractor = None


def get_claim_extractor() -> ClaimExtractor:
    """Get or create singleton claim extractor."""
    global _claim_extractor
    if _claim_extractor is None:
        _claim_extractor = ClaimExtractor()
    return _claim_extractor
