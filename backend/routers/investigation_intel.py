"""Investigation Intelligence Router.

Covers: chain of custody, timeline, confidence, integrity, conflicts,
dependency graph, why-not-certain, what-would-change, reproducibility,
export, annotations, copilot, review readiness, completeness, overrides,
overclaim validation.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/investigation-intel", tags=["Investigation Intelligence"])


# ============================================================
#  CHAIN OF CUSTODY
# ============================================================

class CustodyEventRequest(BaseModel):
    evidence_id: str
    event_type: str
    actor: str = "system"
    previous_state: str | None = None
    new_state: str | None = None
    trace_id: str | None = None
    model_version: str | None = None
    details: dict | None = None


@router.post("/custody/events")
async def record_custody_event(body: CustodyEventRequest):
    from backend.services.chain_of_custody import record_event
    return record_event(**body.model_dump())


@router.get("/custody/{evidence_id}")
async def get_custody_chain(evidence_id: str):
    from backend.services.chain_of_custody import get_chain
    return get_chain(evidence_id)


# ============================================================
#  INVESTIGATION TIMELINE
# ============================================================

class TimelineEventRequest(BaseModel):
    case_id: str
    event_type: str
    description: str = ""
    actor: str = "system"
    module: str | None = None
    evidence_id: str | None = None
    details: dict | None = None


@router.post("/timeline/events")
async def add_timeline_event(body: TimelineEventRequest):
    from backend.services.timeline_service import add_event
    return add_event(**body.model_dump())


@router.get("/investigations/{case_id}/timeline")
async def get_investigation_timeline(
    case_id: str,
    event_type: str | None = None,
    actor: str | None = None,
    module: str | None = None,
):
    from backend.services.timeline_service import get_timeline
    return get_timeline(case_id, event_type=event_type, actor=actor, module=module)


# ============================================================
#  INVESTIGATION CONFIDENCE
# ============================================================

class InvConfidenceRequest(BaseModel):
    model_agreement: float = 0.5
    evidence_quality: float = 0.5
    source_diversity: float = 0.5
    provenance_available: bool = False
    claim_verification: float = 0.5
    cross_modal_agreement: float = 0.5
    contradiction_level: float = 0.0
    data_quality: float = 0.5


@router.post("/investigation-confidence")
async def investigation_confidence(body: InvConfidenceRequest):
    from backend.services.investigation_confidence import compute_investigation_confidence
    return compute_investigation_confidence(**body.model_dump())


# ============================================================
#  INVESTIGATION INTEGRITY SCORE
# ============================================================

class IntegrityRequest(BaseModel):
    evidence_completeness: float = 0.5
    source_diversity: float = 0.5
    model_agreement: float = 0.5
    provenance: float = 0.5
    evidence_consistency: float = 0.5
    reproducibility: float = 0.5
    uncertainty_handled: bool = True


@router.post("/integrity-score")
async def integrity_score(body: IntegrityRequest):
    from backend.services.integrity_score import compute_integrity_score
    return compute_integrity_score(**body.model_dump())


# ============================================================
#  EVIDENCE CONFLICT RESOLVER
# ============================================================

class ConflictRequest(BaseModel):
    evidence_items: list[dict]


@router.post("/conflicts")
async def detect_conflicts(body: ConflictRequest):
    from backend.services.conflict_resolver import detect_and_resolve_conflicts
    return detect_and_resolve_conflicts(body.evidence_items)


# ============================================================
#  EVIDENCE DEPENDENCY GRAPH
# ============================================================

class DependencyRequest(BaseModel):
    evidence_items: list[dict]
    sources: list[dict] | None = None
    model_signals: list[dict] | None = None
    conclusion: dict | None = None


@router.post("/dependency-graph")
async def build_dependency_graph(body: DependencyRequest):
    from backend.services.dependency_graph import build_dependency_graph
    return build_dependency_graph(
        evidence_items=body.evidence_items,
        sources=body.sources,
        model_signals=body.model_signals,
        conclusion=body.conclusion,
    )


class DependencyQueryRequest(BaseModel):
    graph: dict
    evidence_id: str


@router.post("/dependency-graph/query")
async def query_dependency(body: DependencyQueryRequest):
    from backend.services.dependency_graph import query_dependency
    return query_dependency(body.graph, body.evidence_id)


# ============================================================
#  WHY NOT CERTAIN?
# ============================================================

class WhyNotCertainRequest(BaseModel):
    source_available: bool = True
    provenance_available: bool = False
    model_agreement: bool = True
    fact_check_complete: bool = False
    audio_quality_sufficient: bool = True
    evidence_count: int = 0
    contradiction_count: int = 0
    original_source_available: bool = False


@router.post("/why-not-certain")
async def why_not_certain(body: WhyNotCertainRequest):
    from backend.services.why_not_certain import generate_uncertainty_reasons
    return generate_uncertainty_reasons(**body.model_dump())


# ============================================================
#  WHAT WOULD CHANGE MY MIND?
# ============================================================

class WhatWouldChangeRequest(BaseModel):
    has_original_source: bool = False
    has_provenance: bool = False
    has_high_quality_audio: bool = True
    has_independent_source: bool = False
    has_fact_check: bool = False
    has_cross_modal_match: bool = True
    current_risk: float = 50.0


@router.post("/what-would-change")
async def what_would_change(body: WhatWouldChangeRequest):
    from backend.services.what_would_change import identify_missing_evidence
    return identify_missing_evidence(**body.model_dump())


# ============================================================
#  REPRODUCIBILITY
# ============================================================

class ReproduceRequest(BaseModel):
    original_signals: dict
    reproduced_signals: dict
    tolerance: float = 2.0


@router.post("/reproduce")
async def reproduce_analysis(body: ReproduceRequest):
    from backend.services.reproducibility import check_reproducibility
    return check_reproducibility(
        original_signals=body.original_signals,
        reproduced_signals=body.reproduced_signals,
        tolerance=body.tolerance,
    )


class DiffRequest(BaseModel):
    original: dict
    current: dict


@router.post("/diff")
async def analysis_diff(body: DiffRequest):
    from backend.services.reproducibility import compute_analysis_diff
    return compute_analysis_diff(body.original, body.current)


# ============================================================
#  EXPORT PACKAGE
# ============================================================

class ExportRequest(BaseModel):
    investigation: dict
    evidence: list[dict] | None = None
    analyses: list[dict] | None = None
    timeline: list[dict] | None = None
    model_versions: list[dict] | None = None
    audit_log: list[dict] | None = None
    snapshots: list[dict] | None = None
    conflicts: dict | None = None
    integrity: dict | None = None
    include_media: bool = False


@router.post("/export")
async def export_package(body: ExportRequest):
    from backend.services.export_package import build_export_package
    return build_export_package(**body.model_dump())


# ============================================================
#  ANNOTATIONS
# ============================================================

class AnnotationRequest(BaseModel):
    evidence_id: str
    annotation_type: str
    content: str
    author: str = "analyst"
    tags: list[str] | None = None


@router.post("/annotations")
async def add_annotation(body: AnnotationRequest):
    from backend.services.annotation_service import add_annotation
    return add_annotation(**body.model_dump())


@router.get("/annotations/{evidence_id}")
async def get_annotations(evidence_id: str):
    from backend.services.annotation_service import get_annotations
    return get_annotations(evidence_id)


# ============================================================
#  INVESTIGATION COPILOT
# ============================================================

class CopilotRequest(BaseModel):
    question: str
    evidence: list[dict] | None = None
    analyses: list[dict] | None = None
    conflicts: dict | None = None
    uncertainty: dict | None = None
    timeline: list[dict] | None = None
    model_signals: list[dict] | None = None


@router.post("/copilot")
async def copilot_answer(body: CopilotRequest):
    from backend.services.copilot_service import answer_question
    return answer_question(**body.model_dump())


# ============================================================
#  REVIEW READINESS
# ============================================================

class ReviewReadinessRequest(BaseModel):
    evidence_count: int = 0
    has_provenance: bool = False
    has_fact_check: bool = False
    has_source_analysis: bool = False
    conflict_count: int = 0
    uncertainty_level: str = "MEDIUM"
    models_loaded: int = 0


@router.post("/review-readiness")
async def review_readiness(body: ReviewReadinessRequest):
    from backend.services.review_service import compute_review_readiness
    return compute_review_readiness(**body.model_dump())


# ============================================================
#  COMPLETENESS CHECKLIST
# ============================================================

class CompletenessRequest(BaseModel):
    has_media_analyzed: bool = False
    has_claims_extracted: bool = False
    has_sources_reviewed: bool = False
    has_provenance_checked: bool = False
    has_evidence_reviewed: bool = False
    has_conflicts_reviewed: bool = False
    has_uncertainty_assessed: bool = False
    has_model_versions_recorded: bool = False
    has_human_review: bool = False
    has_final_assessment: bool = False


@router.post("/completeness")
async def check_completeness(body: CompletenessRequest):
    from backend.services.review_service import check_investigation_completeness
    return check_investigation_completeness(**body.model_dump())


# ============================================================
#  OVERRIDE TRACKING
# ============================================================

class OverrideRequest(BaseModel):
    case_id: str
    previous_assessment: str
    new_assessment: str
    reviewer: str
    reason: str
    note: str | None = None
    evidence_considered: list[str] | None = None


@router.post("/overrides")
async def track_override(body: OverrideRequest):
    from backend.services.review_service import track_override
    return track_override(**body.model_dump())


@router.get("/overrides/{case_id}")
async def get_overrides(case_id: str):
    from backend.services.review_service import get_overrides
    return get_overrides(case_id)


# ============================================================
#  OVERCLAIM VALIDATOR
# ============================================================

class OverclaimRequest(BaseModel):
    verdict: str
    explanation: str
    risk_score: float


@router.post("/validate-language")
async def validate_language(body: OverclaimRequest):
    from backend.services.overclaim_validator import validate_assessment_language
    return validate_assessment_language(body.verdict, body.explanation, body.risk_score)
