"""Evidence Engine — consumes existing model outputs, never modifies them."""


class EvidenceEngine:
    """Converts model outputs into structured evidence records."""

    def collect_from_analysis(self, analysis: dict) -> list[dict]:
        """Create evidence records from an existing analysis result."""
        evidence = []
        breakdown = analysis.get("breakdown", {})

        for modality in ["text", "image", "video", "audio"]:
            result = breakdown.get(modality)
            if result and isinstance(result, dict) and "label" in result:
                evidence.append({
                    "source_module": modality,
                    "type": f"{modality.upper()}_EVIDENCE",
                    "description": f"{modality.upper()} model: {result['label']} ({result.get('confidence', 0):.1%})",
                    "score": result.get("confidence", 0),
                    "impact": "HIGH" if result.get("confidence", 0) > 0.8 else "MEDIUM",
                    "category": "SUPPORTING" if result.get("label") in ("fake", "cloned") else "NEUTRAL",
                    "status": "COMPLETED",
                })
        return evidence

    def calculate_strength(self, evidence_list: list[dict]) -> float:
        """How strong/reliable is the collected evidence?"""
        if not evidence_list:
            return 0.0
        scores = [e.get("score", 0) for e in evidence_list if e.get("score") is not None]
        return sum(scores) / len(scores) if scores else 0.0

    def calculate_agreement(self, evidence_list: list[dict]) -> float:
        """How consistently do independent sources agree?"""
        if len(evidence_list) < 2:
            return 1.0
        categories = [e.get("category", "NEUTRAL") for e in evidence_list]
        if not categories:
            return 1.0
        from collections import Counter
        counts = Counter(categories)
        return counts.most_common(1)[0][1] / len(categories)
