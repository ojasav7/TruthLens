"""
Cross-Modal Contradiction Engine
Detects contradictions between different modalities and content sources.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Contradiction:
    """Represents a detected contradiction."""
    contradiction_id: str
    type: str  # text_image, text_audio, image_audio, source_media, cross_source
    severity: str  # low, medium, high, critical
    description: str
    evidence: list = field(default_factory=list)
    modalities_involved: list = field(default_factory=list)
    confidence: float = 0.0
    recommendation: str = ""


@dataclass
class ContradictionResult:
    """Result of contradiction analysis."""
    contradictions: list
    total_contradictions: int
    critical_contradictions: int
    consistency_score: float
    modalities_analyzed: list
    summary: str
    recommendations: list = field(default_factory=list)


class ContradictionEngine:
    """Detects contradictions across modalities and sources."""
    
    def analyze_contradictions(self, analysis_results: dict, 
                             content_metadata: dict = None) -> ContradictionResult:
        """Analyze all modalities for contradictions."""
        contradictions = []
        
        # Get individual modality results
        text_result = analysis_results.get("text")
        image_result = analysis_results.get("image")
        audio_result = analysis_results.get("audio")
        video_result = analysis_results.get("video")
        
        modalities_analyzed = [m for m in ["text", "image", "audio", "video"] 
                              if analysis_results.get(m) is not None]
        
        # Check text vs image contradictions
        if text_result and image_result:
            text_image_contradictions = self._check_text_image_contradiction(text_result, image_result)
            contradictions.extend(text_image_contradictions)
        
        # Check text vs audio contradictions
        if text_result and audio_result:
            text_audio_contradictions = self._check_text_audio_contradiction(text_result, audio_result)
            contradictions.extend(text_audio_contradictions)
        
        # Check image vs audio contradictions
        if image_result and audio_result:
            image_audio_contradictions = self._check_image_audio_contradiction(image_result, audio_result)
            contradictions.extend(image_audio_contradictions)
        
        # Check source vs media contradictions
        if content_metadata:
            source_contradictions = self._check_source_media_contradiction(
                content_metadata, analysis_results
            )
            contradictions.extend(source_contradictions)
        
        # Check cross-source contradictions
        if content_metadata and len(modalities_analyzed) > 1:
            cross_source_contradictions = self._check_cross_source_contradiction(
                content_metadata, analysis_results
            )
            contradictions.extend(cross_source_contradictions)
        
        # Calculate statistics
        total = len(contradictions)
        critical = sum(1 for c in contradictions if c.severity == "critical")
        
        # Calculate consistency score (inverse of contradictions)
        if total > 0:
            consistency_score = max(0, 1 - (total * 0.15))
        else:
            consistency_score = 1.0
        
        # Generate summary
        summary = self._generate_summary(contradictions, modalities_analyzed)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(contradictions)
        
        return ContradictionResult(
            contradictions=[self._contradiction_to_dict(c) for c in contradictions],
            total_contradictions=total,
            critical_contradictions=critical,
            consistency_score=consistency_score,
            modalities_analyzed=modalities_analyzed,
            summary=summary,
            recommendations=recommendations,
        )
    
    def _check_text_image_contradiction(self, text_result: dict, image_result: dict) -> list:
        """Check for contradictions between text and image analysis."""
        contradictions = []
        
        text_label = text_result.get("label", "unknown")
        image_label = image_result.get("label", "unknown")
        
        # Check for direct contradictions
        if text_label == "real" and image_label == "fake":
            contradictions.append(Contradiction(
                contradiction_id="text_image_1",
                type="text_image",
                severity="critical",
                description="Text claims content is real, but image analysis shows manipulation",
                evidence=[
                    f"Text analysis: {text_label} (confidence: {text_result.get('confidence', 0):.2f})",
                    f"Image analysis: {image_label} (confidence: {image_result.get('confidence', 0):.2f})",
                ],
                modalities_involved=["text", "image"],
                confidence=0.9,
                recommendation="Verify image authenticity through official sources",
            ))
        
        elif text_label == "fake" and image_label == "real":
            contradictions.append(Contradiction(
                contradiction_id="text_image_2",
                type="text_image",
                severity="high",
                description="Text claims content is fake, but image analysis shows authenticity",
                evidence=[
                    f"Text analysis: {text_label} (confidence: {text_result.get('confidence', 0):.2f})",
                    f"Image analysis: {image_label} (confidence: {image_result.get('confidence', 0):.2f})",
                ],
                modalities_involved=["text", "image"],
                confidence=0.8,
                recommendation="Consider that text may be misinformation about the image",
            ))
        
        return contradictions
    
    def _check_text_audio_contradiction(self, text_result: dict, audio_result: dict) -> list:
        """Check for contradictions between text and audio analysis."""
        contradictions = []
        
        text_label = text_result.get("label", "unknown")
        audio_label = audio_result.get("label", "unknown")
        
        # Check for direct contradictions
        if text_label == "real" and audio_label in ["fake", "cloned"]:
            contradictions.append(Contradiction(
                contradiction_id="text_audio_1",
                type="text_audio",
                severity="critical",
                description="Text claims content is real, but audio shows signs of cloning or generation",
                evidence=[
                    f"Text analysis: {text_label} (confidence: {text_result.get('confidence', 0):.2f})",
                    f"Audio analysis: {audio_label} (confidence: {audio_result.get('confidence', 0):.2f})",
                ],
                modalities_involved=["text", "audio"],
                confidence=0.85,
                recommendation="Verify audio source and speaker identity",
            ))
        
        return contradictions
    
    def _check_image_audio_contradiction(self, image_result: dict, audio_result: dict) -> list:
        """Check for contradictions between image and audio analysis."""
        contradictions = []
        
        image_label = image_result.get("label", "unknown")
        audio_label = audio_result.get("label", "unknown")
        
        # Check for mismatches
        if image_label == "fake" and audio_label == "real":
            contradictions.append(Contradiction(
                contradiction_id="image_audio_1",
                type="image_audio",
                severity="high",
                description="Image shows manipulation but audio appears authentic",
                evidence=[
                    f"Image analysis: {image_label} (confidence: {image_result.get('confidence', 0):.2f})",
                    f"Audio analysis: {audio_label} (confidence: {audio_result.get('confidence', 0):.2f})",
                ],
                modalities_involved=["image", "audio"],
                confidence=0.75,
                recommendation="Investigate if image was altered while audio remains genuine",
            ))
        
        elif image_label == "real" and audio_label in ["fake", "cloned"]:
            contradictions.append(Contradiction(
                contradiction_id="image_audio_2",
                type="image_audio",
                severity="high",
                description="Image appears authentic but audio shows cloning indicators",
                evidence=[
                    f"Image analysis: {image_label} (confidence: {image_result.get('confidence', 0):.2f})",
                    f"Audio analysis: {audio_label} (confidence: {audio_result.get('confidence', 0):.2f})",
                ],
                modalities_involved=["image", "audio"],
                confidence=0.8,
                recommendation="Verify if audio was generated or cloned from original speaker",
            ))
        
        return contradictions
    
    def _check_source_media_contradiction(self, metadata: dict, analysis_results: dict) -> list:
        """Check for contradictions between claimed source and media analysis."""
        contradictions = []
        
        claimed_source = metadata.get("claimed_source", "")
        source_credibility = metadata.get("source_credibility", 0.5)
        
        # Check if source claims don't match media analysis
        for modality, result in analysis_results.items():
            if result is None:
                continue
            
            label = result.get("label", "unknown")
            confidence = result.get("confidence", 0)
            
            # If source claims authenticity but media shows manipulation
            if source_credibility > 0.7 and label == "fake" and confidence > 0.7:
                contradictions.append(Contradiction(
                    contradiction_id=f"source_{modality}_1",
                    type="source_media",
                    severity="critical",
                    description=f"Credible source ({claimed_source}) but {modality} analysis shows manipulation",
                    evidence=[
                        f"Source: {claimed_source} (credibility: {source_credibility:.2f})",
                        f"{modality.capitalize()} analysis: {label} (confidence: {confidence:.2f})",
                    ],
                    modalities_involved=[modality],
                    confidence=0.85,
                    recommendation=f"Verify {modality} content independently",
                ))
        
        return contradictions
    
    def _check_cross_source_contradiction(self, metadata: dict, analysis_results: dict) -> list:
        """Check for contradictions between different sources."""
        contradictions = []
        
        sources = metadata.get("sources", [])
        if len(sources) < 2:
            return contradictions
        
        # Check for source disagreements
        source_claims = {}
        for source in sources:
            source_name = source.get("name", "")
            source_claim = source.get("claim", "")
            source_credibility = source.get("credibility", 0.5)
            
            if source_name and source_claim:
                source_claims[source_name] = {
                    "claim": source_claim,
                    "credibility": source_credibility,
                }
        
        # Compare source claims
        source_names = list(source_claims.keys())
        for i in range(len(source_names)):
            for j in range(i + 1, len(source_names)):
                source1 = source_claims[source_names[i]]
                source2 = source_claims[source_names[j]]
                
                if source1["claim"] != source2["claim"]:
                    contradictions.append(Contradiction(
                        contradiction_id=f"cross_source_{i}_{j}",
                        type="cross_source",
                        severity="medium",
                        description=f"Sources disagree: {source_names[i]} says '{source1['claim']}', {source_names[j]} says '{source2['claim']}'",
                        evidence=[
                            f"{source_names[i]}: {source1['claim']} (credibility: {source1['credibility']:.2f})",
                            f"{source_names[j]}: {source2['claim']} (credibility: {source2['credibility']:.2f})",
                        ],
                        modalities_involved=[],
                        confidence=0.7,
                        recommendation="Consider source credibility when evaluating conflicting claims",
                    ))
        
        return contradictions
    
    def _generate_summary(self, contradictions: list, modalities: list) -> str:
        """Generate a summary of contradictions."""
        if not contradictions:
            return f"No contradictions detected across {len(modalities)} modalities analyzed."
        
        critical = sum(1 for c in contradictions if c.severity == "critical")
        high = sum(1 for c in contradictions if c.severity == "high")
        medium = sum(1 for c in contradictions if c.severity == "medium")
        
        summary_parts = []
        summary_parts.append(f"Found {len(contradictions)} contradiction(s) across {len(modalities)} modalities.")
        
        if critical > 0:
            summary_parts.append(f"{critical} critical contradiction(s) require immediate attention.")
        if high > 0:
            summary_parts.append(f"{high} high-severity contradiction(s) detected.")
        if medium > 0:
            summary_parts.append(f"{medium} medium-severity contradiction(s) noted.")
        
        return " ".join(summary_parts)
    
    def _generate_recommendations(self, contradictions: list) -> list:
        """Generate recommendations based on contradictions."""
        recommendations = []
        
        if not contradictions:
            recommendations.append({
                "action": "Continue monitoring",
                "priority": "low",
                "description": "No contradictions detected. Content appears consistent across modalities.",
            })
            return recommendations
        
        critical = [c for c in contradictions if c.severity == "critical"]
        high = [c for c in contradictions if c.severity == "high"]
        
        if critical:
            recommendations.append({
                "action": "Investigate immediately",
                "priority": "high",
                "description": f"{len(critical)} critical contradiction(s) found. Manual investigation required.",
            })
        
        if high:
            recommendations.append({
                "action": "Verify with additional sources",
                "priority": "medium",
                "description": f"{len(high)} high-severity contradiction(s) found. Cross-reference with trusted sources.",
            })
        
        recommendations.append({
            "action": "Review all modalities",
            "priority": "medium",
            "description": "Contradictions suggest potential manipulation. Review each modality independently.",
        })
        
        return recommendations
    
    def _contradiction_to_dict(self, contradiction: Contradiction) -> dict:
        """Convert contradiction to dictionary."""
        return {
            "contradiction_id": contradiction.contradiction_id,
            "type": contradiction.type,
            "severity": contradiction.severity,
            "description": contradiction.description,
            "evidence": contradiction.evidence,
            "modalities_involved": contradiction.modalities_involved,
            "confidence": contradiction.confidence,
            "recommendation": contradiction.recommendation,
        }


# Singleton instance
_contradiction_engine = None


def get_contradiction_engine() -> ContradictionEngine:
    """Get or create singleton contradiction engine."""
    global _contradiction_engine
    if _contradiction_engine is None:
        _contradiction_engine = ContradictionEngine()
    return _contradiction_engine
