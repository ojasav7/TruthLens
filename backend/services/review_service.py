"""Review Readiness, Completeness Checklist, and Override Tracking."""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.review")

# In-memory override store
_overrides: dict[str, list[dict]] = {}


# --- Review Readiness ---

def compute_review_readiness(
    evidence_count: int = 0,
    has_provenance: bool = False,
    has_fact_check: bool = False,
    has_source_analysis: bool = False,
    conflict_count: int = 0,
    uncertainty_level: str = "MEDIUM",
    models_loaded: int = 0,
) -> dict:
    """Compute review readiness score before sending to human review."""
    checks = {
        "evidence_gathered": evidence_count >= 2,
        "provenance_checked": has_provenance,
        "fact_check_done": has_fact_check,
        "sources_reviewed": has_source_analysis,
        "conflicts_documented": True,  # always true if we got here
        "uncertainty_assessed": uncertainty_level in ("LOW", "MEDIUM"),
    }
    passed = sum(checks.values())
    total = len(checks)
    readiness = round(passed / total * 100, 1) if total > 0 else 0

    priority = "LOW"
    if uncertainty_level in ("HIGH", "CRITICAL"):
        priority = "HIGH"
    elif conflict_count >= 2:
        priority = "HIGH"
    elif readiness < 50:
        priority = "HIGH"
    elif readiness < 80:
        priority = "MEDIUM"

    return {
        "readiness_score": readiness,
        "checks": checks,
        "conflict_level": "HIGH" if conflict_count >= 2 else "MEDIUM" if conflict_count == 1 else "LOW",
        "recommended_priority": priority,
        "ready_for_review": readiness >= 60,
        "summary": f"Review readiness: {readiness:.0f}%. {total - passed} check(s) incomplete.",
    }


# --- Completeness Checklist ---

def check_investigation_completeness(
    has_media_analyzed: bool = False,
    has_claims_extracted: bool = False,
    has_sources_reviewed: bool = False,
    has_provenance_checked: bool = False,
    has_evidence_reviewed: bool = False,
    has_conflicts_reviewed: bool = False,
    has_uncertainty_assessed: bool = False,
    has_model_versions_recorded: bool = False,
    has_human_review: bool = False,
    has_final_assessment: bool = False,
) -> dict:
    """Check if investigation is complete before marking as done."""
    checklist = {
        "media_analyzed": has_media_analyzed,
        "claims_extracted": has_claims_extracted,
        "sources_reviewed": has_sources_reviewed,
        "provenance_checked": has_provenance_checked,
        "evidence_reviewed": has_evidence_reviewed,
        "conflicts_reviewed": has_conflicts_reviewed,
        "uncertainty_assessed": has_uncertainty_assessed,
        "model_versions_recorded": has_model_versions_recorded,
        "human_review_completed": has_human_review,
        "final_assessment_documented": has_final_assessment,
    }
    completed = sum(checklist.values())
    total = len(checklist)
    is_complete = completed == total

    missing = [k for k, v in checklist.items() if not v]

    return {
        "is_complete": is_complete,
        "completion_pct": round(completed / total * 100, 1) if total > 0 else 0,
        "checklist": checklist,
        "missing_items": missing,
        "summary": "Investigation is complete." if is_complete else f"Investigation incomplete — {len(missing)} item(s) missing: {', '.join(missing)}.",
    }


# --- Override Tracking ---

def track_override(
    case_id: str,
    previous_assessment: str,
    new_assessment: str,
    reviewer: str,
    reason: str,
    note: str | None = None,
    evidence_considered: list[str] | None = None,
) -> dict:
    """Record a human override of the system assessment."""
    override = {
        "id": str(uuid.uuid4())[:12],
        "case_id": case_id,
        "previous_assessment": previous_assessment,
        "new_assessment": new_assessment,
        "reviewer": reviewer,
        "reason": reason,
        "note": note,
        "evidence_considered": evidence_considered or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _overrides.setdefault(case_id, []).append(override)
    logger.info("Override: %s → %s by %s (reason: %s)", previous_assessment, new_assessment, reviewer, reason)
    return override


def get_overrides(case_id: str) -> list[dict]:
    """Get all overrides for a case."""
    return list(_overrides.get(case_id, []))
