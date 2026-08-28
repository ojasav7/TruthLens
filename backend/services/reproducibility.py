"""Reproducible Analysis Mode + Analysis Difference View.

Determines whether a previous analysis can be reproduced.
Compares original vs reproduced signals, not just final scores.
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.reproduce")


@dataclass
class ReproductionResult:
    status: str  # REPRODUCIBLE, RESULT_DIFFERENCE, MODULE_DIFFERENCE
    original_risk: float
    reproduced_risk: float
    risk_difference: float
    signal_changes: list[dict] = field(default_factory=list)
    model_version_changes: dict = field(default_factory=dict)
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AnalysisDiff:
    field: str
    original: str
    current: str
    delta: str

    def to_dict(self):
        return asdict(self)


def check_reproducibility(
    original_signals: dict,
    reproduced_signals: dict,
    tolerance: float = 2.0,
) -> dict:
    """Compare original and reproduced analysis signals."""
    signal_changes = []
    original_risk = original_signals.get("risk_score", 0)
    reproduced_risk = reproduced_signals.get("risk_score", 0)
    risk_diff = abs(original_risk - reproduced_risk)

    # Compare per-modality signals
    for mod in ["text", "image", "video", "audio"]:
        orig = original_signals.get(mod, {})
        repro = reproduced_signals.get(mod, {})
        if orig and repro:
            orig_conf = orig.get("confidence", 0)
            repro_conf = repro.get("confidence", 0)
            diff = abs(orig_conf - repro_conf)
            if diff > tolerance / 100:
                signal_changes.append({
                    "modality": mod,
                    "original_confidence": orig_conf,
                    "reproduced_confidence": repro_conf,
                    "difference": round(diff, 4),
                })

    # Determine status
    if risk_diff <= tolerance and not signal_changes:
        status = "REPRODUCIBLE"
        summary = f"Analysis is reproducible within {tolerance}% tolerance."
    elif risk_diff <= tolerance and signal_changes:
        status = "MODULE_DIFFERENCE"
        summary = f"Final score stable ({risk_diff:.1f}% diff) but {len(signal_changes)} underlying signal(s) changed."
    else:
        status = "RESULT_DIFFERENCE"
        summary = f"Result difference detected: {risk_diff:.1f}% risk score change."

    # Model version changes
    model_changes = {}
    for mod in ["text", "image", "video", "audio"]:
        v1 = original_signals.get(f"{mod}_version", "unknown")
        v2 = reproduced_signals.get(f"{mod}_version", "unknown")
        if v1 != v2:
            model_changes[mod] = {"original": v1, "reproduced": v2}

    return ReproductionResult(
        status=status,
        original_risk=original_risk,
        reproduced_risk=reproduced_risk,
        risk_difference=round(risk_diff, 2),
        signal_changes=signal_changes,
        model_version_changes=model_changes,
        summary=summary,
    ).to_dict()


def compute_analysis_diff(
    original: dict,
    current: dict,
) -> dict:
    """Compute difference between two analyses."""
    diffs = []
    compare_fields = [
        ("threat_score", "Risk Score"),
        ("verdict", "Verdict"),
    ]

    for field_key, label in compare_fields:
        v1 = original.get(field_key)
        v2 = current.get(field_key)
        if v1 != v2:
            diffs.append(AnalysisDiff(
                field=label,
                original=str(v1),
                current=str(v2),
                delta=f"{v1} → {v2}",
            ).to_dict())

    # Per-modality diffs
    for mod in ["text", "image", "video", "audio"]:
        b1 = (original.get("breakdown") or {}).get(mod, {})
        b2 = (current.get("breakdown") or {}).get(mod, {})
        if b1 and b2:
            c1 = b1.get("confidence", 0)
            c2 = b2.get("confidence", 0)
            if abs(c1 - c2) > 0.01:
                diffs.append(AnalysisDiff(
                    field=f"{mod.upper()} confidence",
                    original=f"{c1:.1%}",
                    current=f"{c2:.1%}",
                    delta=f"{c1:.1%} → {c2:.1%}",
                ).to_dict())

    # Evidence count diff
    e1 = len(original.get("evidence_ids") or [])
    e2 = len(current.get("evidence_ids") or [])
    if e1 != e2:
        diffs.append(AnalysisDiff(
            field="Evidence Count",
            original=str(e1),
            current=str(e2),
            delta=f"{e1} → {e2}",
        ).to_dict())

    return {
        "diffs": diffs,
        "total_changes": len(diffs),
        "summary": f"{len(diffs)} difference(s) detected between analyses." if diffs else "No differences detected.",
    }
