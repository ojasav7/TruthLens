"""Video Temporal Investigation — groups per-frame scores into suspicious segments."""

RISK_THRESHOLD = 0.6  # frames above this are "suspicious"


def analyze_timeline(per_frame_scores: list[float], fps: float = 10.0) -> dict:
    """Convert per-frame scores into a timeline with suspicious segments."""
    if not per_frame_scores:
        return {"segments": [], "total_frames": 0, "suspicious_frames": 0}

    segments = []
    current_seg = None
    suspicious_count = 0

    for i, score in enumerate(per_frame_scores):
        timestamp = round(i / fps, 1)
        if score >= RISK_THRESHOLD:
            suspicious_count += 1
            if current_seg is None:
                current_seg = {"start": timestamp, "end": timestamp, "max_risk": score, "frame_count": 1}
            else:
                current_seg["end"] = timestamp
                current_seg["max_risk"] = max(current_seg["max_risk"], score)
                current_seg["frame_count"] += 1
        else:
            if current_seg is not None:
                segments.append(current_seg)
                current_seg = None

    if current_seg is not None:
        segments.append(current_seg)

    # Round max_risk in output
    for seg in segments:
        seg["max_risk"] = round(seg["max_risk"], 2)

    return {
        "segments": segments,
        "total_frames": len(per_frame_scores),
        "suspicious_frames": suspicious_count,
        "risk_percentage": round(suspicious_count / len(per_frame_scores) * 100, 1),
    }
