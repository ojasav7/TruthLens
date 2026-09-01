"""
Explainability Service
Provides human-friendly explanations beyond model internals,
including SHAP-like feature importance and Grad-CAM-like visual explanations.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Explanation:
    """Human-friendly explanation of model decision."""
    summary: str
    confidence_factors: list = field(default_factory=list)
    key_indicators: list = field(default_factory=list)
    visual_attention: dict = field(default_factory=dict)
    feature_importance: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    technical_details: dict = field(default_factory=dict)


class ExplainabilityService:
    """Provides human-friendly explanations for model decisions."""
    
    # Feature descriptions for different modalities
    FEATURE_DESCRIPTIONS = {
        "text": {
            "lexical_diversity": "Variety of words used in the text",
            "sentiment_score": "Emotional tone of the content",
            "readability_score": "How easy the text is to understand",
            "source_credibility": "Trustworthiness of the claimed source",
            "fact_check_score": "Alignment with known facts",
            "emotional_appeal": "Use of emotionally charged language",
            "source_diversity": "Number of different sources cited",
        },
        "image": {
            "frequency_artifacts": "Anomalies in frequency domain patterns",
            "noise_patterns": "Unusual noise characteristics",
            "color_inconsistencies": "Color distribution anomalies",
            "edge_artifacts": "Edge detection anomalies",
            "texture_analysis": "Texture pattern analysis",
            "compression_artifacts": "JPEG compression anomalies",
            "metadata_consistency": "EXIF metadata alignment",
        },
        "audio": {
            "frequency_spectrum": "Voice frequency characteristics",
            "temporal_consistency": "Timing and rhythm patterns",
            "background_noise": "Environmental noise analysis",
            "voice_clone_signs": "Signs of AI-generated voice",
            "emotional_markers": "Emotional expression patterns",
            "breathing_patterns": "Natural breathing detection",
            "spectral_artifacts": "Spectral analysis anomalies",
        },
        "video": {
            "frame_consistency": "Frame-to-frame consistency",
            "temporal_coherence": "Motion and timing analysis",
            "face_tracking": "Facial feature tracking",
            "lip_sync_accuracy": "Lip movement alignment",
            "background_stability": "Background consistency",
            "lighting_consistency": "Lighting pattern analysis",
            "compression_analysis": "Video compression artifacts",
        },
    }
    
    def explain_decision(self, modality: str, prediction: dict, 
                        input_data: dict = None) -> Explanation:
        """Generate human-friendly explanation for a model decision."""
        label = prediction.get("label", "unknown")
        confidence = prediction.get("confidence", 0)
        signals = prediction.get("signals", {})
        
        # Generate summary
        summary = self._generate_summary(modality, label, confidence)
        
        # Generate confidence factors
        confidence_factors = self._analyze_confidence_factors(modality, signals)
        
        # Generate key indicators
        key_indicators = self._extract_key_indicators(modality, label, signals)
        
        # Generate visual attention (for image/video)
        visual_attention = self._generate_visual_attention(modality, signals)
        
        # Generate feature importance
        feature_importance = self._calculate_feature_importance(modality, signals)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(modality, label, confidence)
        
        return Explanation(
            summary=summary,
            confidence_factors=confidence_factors,
            key_indicators=key_indicators,
            visual_attention=visual_attention,
            feature_importance=feature_importance,
            recommendations=recommendations,
            technical_details={
                "modality": modality,
                "label": label,
                "confidence": confidence,
                "signals_analyzed": len(signals),
            },
        )
    
    def explain_text_analysis(self, text: str, prediction: dict) -> Explanation:
        """Explain text analysis results."""
        return self.explain_decision("text", prediction, {"text": text})
    
    def explain_image_analysis(self, image_info: dict, prediction: dict) -> Explanation:
        """Explain image analysis results."""
        return self.explain_decision("image", prediction, image_info)
    
    def explain_audio_analysis(self, audio_info: dict, prediction: dict) -> Explanation:
        """Explain audio analysis results."""
        return self.explain_decision("audio", prediction, audio_info)
    
    def explain_video_analysis(self, video_info: dict, prediction: dict) -> Explanation:
        """Explain video analysis results."""
        return self.explain_decision("video", prediction, video_info)
    
    def _generate_summary(self, modality: str, label: str, confidence: float) -> str:
        """Generate a human-readable summary."""
        modality_name = modality.capitalize()
        
        if label == "fake" or label == "cloned":
            if confidence > 0.8:
                return f"The {modality_name} analysis strongly indicates this content is not authentic. Multiple indicators point to manipulation or generation."
            elif confidence > 0.6:
                return f"The {modality_name} analysis suggests this content may be manipulated. Several suspicious patterns were detected."
            else:
                return f"The {modality_name} analysis found some unusual patterns, but we're not certain about authenticity."
        elif label == "real" or label == "genuine":
            if confidence > 0.8:
                return f"The {modality_name} analysis strongly indicates this content is authentic. No significant manipulation signs were found."
            elif confidence > 0.6:
                return f"The {modality_name} analysis suggests this content is likely authentic, with minor anomalies detected."
            else:
                return f"The {modality_name} analysis found this content appears mostly authentic, but some uncertainty remains."
        else:
            return f"The {modality_name} analysis was unable to definitively determine the authenticity of this content."
    
    def _analyze_confidence_factors(self, modality: str, signals: dict) -> list:
        """Analyze factors contributing to confidence score."""
        factors = []
        
        features = self.FEATURE_DESCRIPTIONS.get(modality, {})
        
        for key, description in features.items():
            value = signals.get(key, 0)
            if isinstance(value, (int, float)):
                importance = abs(value) if value else 0
                if importance > 0.3:
                    factors.append({
                        "factor": description,
                        "value": round(value, 3),
                        "importance": round(importance, 3),
                        "impact": "high" if importance > 0.7 else "medium" if importance > 0.5 else "low",
                    })
        
        # Sort by importance
        factors.sort(key=lambda x: x["importance"], reverse=True)
        
        return factors[:10]  # Top 10 factors
    
    def _extract_key_indicators(self, modality: str, label: str, signals: dict) -> list:
        """Extract key indicators that drove the decision."""
        indicators = []
        
        if modality == "text":
            if signals.get("emotional_appeal", 0) > 0.7:
                indicators.append({
                    "indicator": "High emotional appeal",
                    "description": "The text uses emotionally charged language that may be designed to provoke strong reactions.",
                    "severity": "warning",
                })
            if signals.get("fact_check_score", 1) < 0.3:
                indicators.append({
                    "indicator": "Low fact-check alignment",
                    "description": "Claims in the text don't align well with established facts.",
                    "severity": "critical",
                })
            if signals.get("source_credibility", 0.5) < 0.3:
                indicators.append({
                    "indicator": "Low source credibility",
                    "description": "The claimed source has low trustworthiness.",
                    "severity": "warning",
                })
        
        elif modality == "image":
            if signals.get("frequency_artifacts", 0) > 0.7:
                indicators.append({
                    "indicator": "Frequency domain anomalies",
                    "description": "The image shows unusual patterns in frequency analysis, suggesting manipulation.",
                    "severity": "critical",
                })
            if signals.get("compression_artifacts", 0) > 0.6:
                indicators.append({
                    "indicator": "Compression inconsistencies",
                    "description": "Multiple compression levels detected, suggesting the image was modified.",
                    "severity": "warning",
                })
        
        elif modality == "audio":
            if signals.get("voice_clone_signs", 0) > 0.7:
                indicators.append({
                    "indicator": "Voice cloning indicators",
                    "description": "The audio shows patterns consistent with AI-generated or cloned voice.",
                    "severity": "critical",
                })
            if signals.get("temporal_consistency", 0) < 0.3:
                indicators.append({
                    "indicator": "Temporal inconsistencies",
                    "description": "The audio timing and rhythm patterns are unnatural.",
                    "severity": "warning",
                })
        
        elif modality == "video":
            if signals.get("lip_sync_accuracy", 0) < 0.3:
                indicators.append({
                    "indicator": "Lip sync issues",
                    "description": "The lip movements don't match the audio, suggesting deepfake manipulation.",
                    "severity": "critical",
                })
            if signals.get("face_tracking", 0) < 0.4:
                indicators.append({
                    "indicator": "Facial feature anomalies",
                    "description": "The facial features show unnatural movements or distortions.",
                    "severity": "warning",
                })
        
        return indicators
    
    def _generate_visual_attention(self, modality: str, signals: dict) -> dict:
        """Generate visual attention map (for Grad-CAM-like explanations)."""
        if modality not in ["image", "video"]:
            return {}
        
        attention_regions = []
        
        if modality == "image":
            # Simulate attention regions
            attention_regions = [
                {
                    "region": "face",
                    "importance": signals.get("face_analysis", 0.5),
                    "description": "Facial features and expressions",
                    "coordinates": {"x": 0.3, "y": 0.2, "width": 0.4, "height": 0.5},
                },
                {
                    "region": "background",
                    "importance": signals.get("background_analysis", 0.3),
                    "description": "Background elements and consistency",
                    "coordinates": {"x": 0, "y": 0, "width": 1, "height": 1},
                },
                {
                    "region": "edges",
                    "importance": signals.get("edge_analysis", 0.4),
                    "description": "Edge detection and sharpness",
                    "coordinates": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6},
                },
            ]
        
        elif modality == "video":
            attention_regions = [
                {
                    "region": "face",
                    "importance": signals.get("face_tracking", 0.6),
                    "description": "Facial feature tracking over time",
                    "coordinates": {"x": 0.3, "y": 0.2, "width": 0.4, "height": 0.5},
                },
                {
                    "region": "lips",
                    "importance": signals.get("lip_sync_accuracy", 0.7),
                    "description": "Lip movement alignment with audio",
                    "coordinates": {"x": 0.4, "y": 0.5, "width": 0.2, "height": 0.1},
                },
                {
                    "region": "eyes",
                    "importance": signals.get("eye_tracking", 0.5),
                    "description": "Eye movement and blinking patterns",
                    "coordinates": {"x": 0.35, "y": 0.3, "width": 0.3, "height": 0.1},
                },
            ]
        
        return {
            "regions": attention_regions,
            "method": "Grad-CAM" if modality == "image" else "Temporal Attention",
            "description": f"Visual attention map showing which regions most influenced the {modality} analysis",
        }
    
    def _calculate_feature_importance(self, modality: str, signals: dict) -> list:
        """Calculate feature importance (SHAP-like)."""
        features = []
        
        modality_features = self.FEATURE_DESCRIPTIONS.get(modality, {})
        
        for key, description in modality_features.items():
            value = signals.get(key, 0)
            if isinstance(value, (int, float)):
                # SHAP-like importance (simplified)
                importance = abs(value) * 0.8  # Simplified SHAP value
                direction = "positive" if value > 0 else "negative"
                
                features.append({
                    "feature": description,
                    "feature_key": key,
                    "value": round(value, 3),
                    "importance": round(importance, 3),
                    "direction": direction,
                    "shap_value": round(importance * (1 if direction == "positive" else -1), 3),
                })
        
        # Sort by importance
        features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        return features
    
    def _generate_recommendations(self, modality: str, label: str, confidence: float) -> list:
        """Generate actionable recommendations."""
        recommendations = []
        
        if label in ["fake", "cloned"]:
            if confidence > 0.8:
                recommendations.append({
                    "action": "Do not share",
                    "priority": "high",
                    "description": "This content shows strong signs of manipulation. Do not share until verified.",
                })
                recommendations.append({
                    "action": "Verify with official sources",
                    "priority": "high",
                    "description": "Check official channels or trusted news sources for verification.",
                })
            elif confidence > 0.6:
                recommendations.append({
                    "action": "Exercise caution",
                    "priority": "medium",
                    "description": "This content may be manipulated. Verify before sharing.",
                })
                recommendations.append({
                    "action": "Cross-reference sources",
                    "priority": "medium",
                    "description": "Look for corroborating reports from multiple trusted sources.",
                })
        elif label in ["real", "genuine"]:
            recommendations.append({
                "action": "Content appears authentic",
                "priority": "low",
                "description": "No significant manipulation signs detected.",
            })
            if confidence < 0.7:
                recommendations.append({
                    "action": "Consider additional verification",
                    "priority": "low",
                    "description": "While likely authentic, consider verifying with official sources for high-stakes content.",
                })
        
        return recommendations


# Singleton instance
_explainability_service = None


def get_explainability_service() -> ExplainabilityService:
    """Get or create singleton explainability service."""
    global _explainability_service
    if _explainability_service is None:
        _explainability_service = ExplainabilityService()
    return _explainability_service
