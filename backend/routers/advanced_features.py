"""Advanced Features Router — 8 capabilities for misinformation investigation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


class SourceVerifyReq(BaseModel):
    url: str


class ClaimReq(BaseModel):
    text: str


class ReviewReq(BaseModel):
    analysis_id: str
    reviewer_id: str


class CommentReq(BaseModel):
    analysis_id: str
    reviewer_id: str
    comment: str


class VerdictReq(BaseModel):
    analysis_id: str
    reviewer_id: str
    new_verdict: str
    reason: str


class DispositionReq(BaseModel):
    analysis_id: str
    reviewer_id: str
    disposition: str


class ExplainReq(BaseModel):
    modality: str
    prediction: dict


class ContradictionReq(BaseModel):
    analysis_results: dict
    metadata: Optional[dict] = None


# --- Feature 1: Source Verification ---

@router.post("/source-verify")
async def verify_source(req: SourceVerifyReq):
    from backend.services.source_verification import verify_source as verify
    return verify(req.url)


# --- Feature 2: Claim Extraction ---

@router.post("/claims/extract")
async def extract_claims(req: ClaimReq):
    from backend.services.claim_extraction import extract_claims
    return extract_claims(req.text)


@router.post("/claims/match")
async def match_evidence(req: ClaimReq):
    from backend.services.claim_extraction import match_evidence
    return match_evidence(req.text)


# --- Feature 3: Review Workflow ---

@router.post("/review/assign")
async def assign_reviewer(req: ReviewReq):
    from backend.services.review_workflow import assign_reviewer
    return assign_reviewer(req.analysis_id, req.reviewer_id)


@router.post("/review/comment")
async def add_comment(req: CommentReq):
    from backend.services.review_workflow import add_comment
    return add_comment(req.analysis_id, req.reviewer_id, req.comment)


@router.post("/review/override")
async def override_verdict(req: VerdictReq):
    from backend.services.review_workflow import override_verdict
    return override_verdict(req.analysis_id, req.reviewer_id, req.new_verdict, req.reason)


@router.post("/review/disposition")
async def set_disposition(req: DispositionReq):
    from backend.services.review_workflow import set_disposition
    return set_disposition(req.analysis_id, req.reviewer_id, req.disposition)


@router.get("/review/audit/{analysis_id}")
async def get_audit_trail(analysis_id: str):
    from backend.services.review_workflow import get_audit_trail
    return {"analysis_id": analysis_id, "audit_trail": get_audit_trail(analysis_id)}


# --- Feature 4: Timeline ---

@router.post("/timeline/event")
async def add_timeline_event(content_id: str, event_type: str, source: str):
    from backend.services.timeline_service import add_event
    return add_event(content_id, event_type, source)


@router.get("/timeline/{content_id}")
async def get_timeline(content_id: str):
    from backend.services.timeline_service import get_timeline
    return get_timeline(content_id)


# --- Feature 5: Explainability ---

@router.post("/explain")
async def explain_decision(req: ExplainReq):
    from backend.services.explainability import explain
    return explain(req.modality, req.prediction)


# --- Feature 6: Contradiction Engine ---

@router.post("/contradictions")
async def analyze_contradictions(req: ContradictionReq):
    from backend.services.contradiction_engine import analyze_contradictions
    return analyze_contradictions(req.analysis_results, req.metadata)


# --- Feature 7: Calibration Dashboard ---

@router.get("/calibration/dashboard")
async def get_dashboard():
    from backend.services.calibration_dashboard import get_dashboard
    return get_dashboard()


@router.get("/calibration/modalities")
async def get_modality_performance():
    from backend.services.calibration_dashboard import get_modality_performance
    return get_modality_performance()


# --- Feature 8: Benchmark ---

@router.get("/benchmark/summary")
async def get_benchmark_summary():
    from backend.services.calibration_dashboard import get_dashboard
    return get_dashboard()["benchmark_results"]
