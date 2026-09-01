"""Contradiction Engine — detects contradictions across modalities."""


def analyze_contradictions(analysis_results: dict, metadata: dict = None) -> dict:
    contradictions = []
    text = analysis_results.get("text")
    image = analysis_results.get("image")
    audio = analysis_results.get("audio")
    modalities = [m for m in ["text", "image", "audio", "video"] if analysis_results.get(m)]

    # Text vs Image
    if text and image:
        tl, il = text.get("label"), image.get("label")
        if tl == "real" and il == "fake":
            contradictions.append({"type": "text_image", "severity": "critical",
                "description": "Text claims real but image shows manipulation"})
        elif tl == "fake" and il == "real":
            contradictions.append({"type": "text_image", "severity": "high",
                "description": "Text claims fake but image appears authentic"})

    # Text vs Audio
    if text and audio:
        tl, al = text.get("label"), audio.get("label")
        if tl == "real" and al in ("fake", "cloned"):
            contradictions.append({"type": "text_audio", "severity": "critical",
                "description": "Text claims real but audio shows cloning"})

    # Image vs Audio
    if image and audio:
        il, al = image.get("label"), audio.get("label")
        if il == "fake" and al == "real":
            contradictions.append({"type": "image_audio", "severity": "high",
                "description": "Image manipulated but audio authentic"})
        elif il == "real" and al in ("fake", "cloned"):
            contradictions.append({"type": "image_audio", "severity": "high",
                "description": "Image authentic but audio cloned"})

    # Source vs Media
    if metadata and metadata.get("source_credibility", 0.5) > 0.7:
        for modality, result in analysis_results.items():
            if result and result.get("label") == "fake" and result.get("confidence", 0) > 0.7:
                contradictions.append({"type": "source_media", "severity": "critical",
                    "description": f"Credible source but {modality} shows manipulation"})

    total = len(contradictions)
    consistency = max(0, 1 - total * 0.15) if total else 1.0
    critical = sum(1 for c in contradictions if c["severity"] == "critical")

    return {
        "contradictions": contradictions,
        "total_contradictions": total,
        "critical_contradictions": critical,
        "consistency_score": round(consistency, 2),
        "modalities_analyzed": modalities,
    }
