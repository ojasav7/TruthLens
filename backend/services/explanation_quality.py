"""Explanation Quality Check.

Before showing an explanation, verify it's supported by actual evidence.
Maps explanations to model signals, evidence items, sources, provenance.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.explanation_quality")


@dataclass
class QualityCheck:
    explanation_text: str
    is_supported: bool
    supporting_evidence: list[str]
    confidence_in_explanation: str  # HIGH, MEDIUM, LOW
    warning: str | None = None

    def to_dict(self):
        return asdict(self)


def verify_explanation(
    explanation: str,
    has_model_signal: bool = False,
    has_evidence: bool = False,
    has_provenance: bool = False,
    has_fact_check: bool = False,
    evidence_count: int = 0,
) -> dict:
    """Check if an explanation is supported by available evidence."""
    supporting = []
    if has_model_signal:
        supporting.append("model_prediction")
    if has_evidence:
        supporting.append("evidence_items")
    if has_provenance:
        supporting.append("provenance_data")
    if has_fact_check:
        supporting.append("fact_check_result")

    supported = len(supporting) >= 1
    confidence = "HIGH" if len(supporting) >= 3 else "MEDIUM" if len(supporting) >= 2 else "LOW"

    warning = None
    if not supported:
        warning = "No supporting evidence found — explanation may not be reliable"
        logger.warning("Explanation not supported by any evidence")
    elif confidence == "LOW":
        warning = "Explanation supported by limited evidence"

    return QualityCheck(
        explanation_text=explanation,
        is_supported=supported,
        supporting_evidence=supporting,
        confidence_in_explanation=confidence,
        warning=warning,
    ).to_dict()


def rewrite_if_unsupported(explanation: str, is_supported: bool) -> str:
    """Rewrite explanation with appropriate hedging if not well-supported."""
    if is_supported:
        return explanation
    # Add hedging language
    hedged = explanation
    replacements = [
        ("was created using AI", "contains visual signals associated with synthetic manipulation"),
        ("is fake", "shows elevated manipulation indicators"),
        ("is authentic", "does not show significant manipulation signals"),
        ("This source is fake", "The source could not be independently verified"),
        ("definitely", "likely"),
    ]
    for old, new in replacements:
        hedged = hedged.replace(old, new)
    if hedged == explanation:
        hedged = f"[Limited evidence] {explanation}"
    return hedged
