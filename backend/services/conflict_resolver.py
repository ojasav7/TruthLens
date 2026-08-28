"""Evidence Conflict Resolver.

Identifies and explains conflicting evidence. Never simply picks the
strongest number — explains WHY one signal carries more weight.
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.conflict")

CONFLICT_CATEGORIES = [
    "source_conflict", "model_conflict", "provenance_conflict",
    "temporal_conflict", "metadata_conflict", "cross_modal_conflict",
    "claim_conflict",
]


@dataclass
class ConflictPair:
    evidence_a: dict
    evidence_b: dict
    category: str
    severity: str  # LOW, MEDIUM, HIGH
    resolution: str
    resolution_reasoning: str

    def to_dict(self):
        return asdict(self)


def detect_and_resolve_conflicts(evidence_items: list[dict]) -> dict:
    """Analyze evidence items for conflicts and resolve them."""
    if len(evidence_items) < 2:
        return {
            "conflicts": [],
            "total_conflicts": 0,
            "overall_severity": "NONE",
            "summary": "Insufficient evidence for conflict analysis",
        }

    conflicts = []

    # Check pairwise for label conflicts
    for i in range(len(evidence_items)):
        for j in range(i + 1, len(evidence_items)):
            a = evidence_items[i]
            b = evidence_items[j]
            label_a = a.get("label", a.get("assessment", "unknown"))
            label_b = b.get("label", b.get("assessment", "unknown"))

            if label_a != label_b and label_a != "unknown" and label_b != "unknown":
                # Conflict detected
                category = _classify_conflict(a, b)
                severity = _assess_severity(a, b)
                resolution, reasoning = _resolve(a, b)
                conflicts.append(ConflictPair(
                    evidence_a={"id": a.get("id", "?"), "label": label_a, "confidence": a.get("confidence", 0.5), "source": a.get("source", "unknown")},
                    evidence_b={"id": b.get("id", "?"), "label": label_b, "confidence": b.get("confidence", 0.5), "source": b.get("source", "unknown")},
                    category=category,
                    severity=severity,
                    resolution=resolution,
                    resolution_reasoning=reasoning,
                ).to_dict())

    overall = "NONE"
    if conflicts:
        severities = [c["severity"] for c in conflicts]
        if "HIGH" in severities:
            overall = "HIGH"
        elif "MEDIUM" in severities:
            overall = "MEDIUM"
        else:
            overall = "LOW"

    summary = f"{len(conflicts)} conflict(s) detected" if conflicts else "No evidence conflicts detected"

    return {
        "conflicts": conflicts,
        "total_conflicts": len(conflicts),
        "overall_severity": overall,
        "summary": summary,
    }


def _classify_conflict(a: dict, b: dict) -> str:
    source_a = a.get("source", "")
    source_b = b.get("source", "")
    if "model" in str(source_a) or "model" in str(source_b):
        return "model_conflict"
    if a.get("type") == "provenance" or b.get("type") == "provenance":
        return "provenance_conflict"
    if a.get("modality") and b.get("modality") and a["modality"] != b["modality"]:
        return "cross_modal_conflict"
    return "source_conflict"


def _assess_severity(a: dict, b: dict) -> str:
    conf_a = a.get("confidence", 0.5)
    conf_b = b.get("confidence", 0.5)
    if conf_a > 0.8 and conf_b > 0.8:
        return "HIGH"
    if conf_a > 0.6 and conf_b > 0.6:
        return "MEDIUM"
    return "LOW"


def _resolve(a: dict, b: dict) -> tuple[str, str]:
    """Explain WHY one signal currently carries more weight."""
    conf_a = a.get("confidence", 0.5)
    conf_b = b.get("confidence", 0.5)
    higher = a if conf_a >= conf_b else b
    lower = b if conf_a >= conf_b else a

    resolution = f"Favors {higher.get('label', '?')} from {higher.get('source', '?')}"
    reasoning = (
        f"The current assessment favors {higher.get('label', '?')} because "
        f"{higher.get('source', 'source')} has higher confidence "
        f"({max(conf_a, conf_b):.0%} vs {min(conf_a, conf_b):.0%}). "
        f"Conflicting evidence from {lower.get('source', '?')} is preserved."
    )
    return resolution, reasoning
