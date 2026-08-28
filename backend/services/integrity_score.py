"""Investigation Integrity Score.

Measures the QUALITY OF THE INVESTIGATION — never labeled as "truth score".
Components: evidence completeness, source diversity, model agreement,
provenance, evidence consistency, reproducibility, uncertainty handling.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.integrity")


@dataclass
class IntegrityResult:
    score: float  # 0-100
    components: dict
    summary: str

    def to_dict(self):
        return asdict(self)


_WEIGHTS = {
    "evidence_completeness": 20,
    "source_diversity": 15,
    "model_agreement": 15,
    "provenance": 15,
    "evidence_consistency": 15,
    "reproducibility": 10,
    "uncertainty_handling": 10,
}


def compute_integrity_score(
    evidence_completeness: float = 0.5,   # 0-1
    source_diversity: float = 0.5,        # 0-1
    model_agreement: float = 0.5,         # 0-1
    provenance: float = 0.5,              # 0-1
    evidence_consistency: float = 0.5,    # 0-1
    reproducibility: float = 0.5,         # 0-1
    uncertainty_handled: bool = True,      # was uncertainty explicitly assessed?
) -> dict:
    """Compute investigation integrity score."""
    components = {}
    total = 0.0

    raw = {
        "evidence_completeness": evidence_completeness,
        "source_diversity": source_diversity,
        "model_agreement": model_agreement,
        "provenance": provenance,
        "evidence_consistency": evidence_consistency,
        "reproducibility": reproducibility,
        "uncertainty_handling": 1.0 if uncertainty_handled else 0.2,
    }

    for component, weight in _WEIGHTS.items():
        value = raw.get(component, 0.5)
        points = value * weight
        total += points
        components[component] = {
            "value": round(value * 100, 1),
            "weight": weight,
            "points": round(points, 1),
        }

    total = max(0, min(100, total))

    weak = [k for k, v in components.items() if v["points"] < v["weight"] * 0.4]
    summary = f"Integrity score: {total:.0f}/100"
    if weak:
        summary += f". Weak areas: {', '.join(w.replace('_', ' ') for w in weak)}"

    return IntegrityResult(
        score=round(total, 1),
        components=components,
        summary=summary,
    ).to_dict()
