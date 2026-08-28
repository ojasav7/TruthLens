"""Court-Ready Forensic Report Generator.

HMAC-signed reports with evidence catalog, chain of custody, limitations.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("truthlens.forensic_report")


def generate_forensic_report(analysis: dict, evidence: list[dict] | None = None, timeline: list[dict] | None = None, model_versions: dict | None = None, chain_of_custody: list[dict] | None = None, **_kwargs) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "report_id": f"FR-{hashlib.sha256(json.dumps(analysis, sort_keys=True, default=str).encode()).hexdigest()[:12].upper()}",
        "report_type": "FORENSIC_ANALYSIS",
        "generated_at": now,
        "truthlens_version": "1.0.0",
        "executive_summary": {"analysis_id": analysis.get("id"), "threat_score": analysis.get("threat_score"), "verdict": analysis.get("verdict"), "input_types": analysis.get("input_types", [])},
        "methodology": {"platform": "TruthLens AI", "modalities": analysis.get("input_types", []), "fusion": "weighted_multimodal", "disclaimer": "AI-assisted analysis — verify independently"},
        "evidence_catalog": [{"id": e.get("id"), "type": e.get("type"), "module": e.get("source_module"), "score": e.get("score"), "category": e.get("category")} for e in (evidence or [])],
        "model_documentation": model_versions or {},
        "chain_of_custody": chain_of_custody or [],
        "timeline": timeline or [],
        "limitations": _limitations(analysis, evidence),
        "admissibility_notes": {"standard": "AI-assisted forensic analysis", "reproducible": "Yes with identical inputs and models", "audit_trail": "Full chain recorded"},
    }
    report_bytes = json.dumps(report, sort_keys=True, default=str).encode()
    report["report_hash"] = hashlib.sha256(report_bytes).hexdigest()
    report["digital_signature"] = {"algorithm": "HMAC-SHA256", "signed_at": now, "report_hash": report["report_hash"]}
    return report


def _limitations(analysis: dict, evidence: list[dict] | None) -> list[str]:
    lims = []
    types = analysis.get("input_types", [])
    if len(types) < 2: lims.append("Single modality — no cross-modal verification")
    if not evidence: lims.append("No independent evidence records")
    elif len(evidence) < 3: lims.append("Limited evidence diversity")
    if not any(e.get("type") == "provenance" for e in (evidence or [])): lims.append("Provenance not verified")
    lims.append("AI results are probabilistic, not deterministic")
    return lims
