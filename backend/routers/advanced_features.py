"""Advanced Features Router — provenance, claims, investigation, explainability, benchmarks."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


class UrlReq(BaseModel):
    url: str


class TextReq(BaseModel):
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


class BenchmarkEvalReq(BaseModel):
    modality: str
    predictions: list[dict]


class MetadataReq(BaseModel):
    metadata: dict


class ReverseImageReq(BaseModel):
    image_hash: str


# --- 1. Provenance Verification ---

@router.post("/source-verify")
async def verify_source(req: UrlReq):
    from backend.services.provenance import verify_source
    return verify_source(req.url)


@router.post("/url-reputation")
async def check_url_reputation(req: UrlReq):
    from backend.services.provenance import check_url_reputation
    return check_url_reputation(req.url)


@router.post("/validate-metadata")
async def validate_metadata(req: MetadataReq):
    from backend.services.provenance import validate_metadata
    return validate_metadata(req.metadata)


@router.post("/reverse-image")
async def reverse_image_check(req: ReverseImageReq):
    from backend.services.provenance import reverse_image_check
    return reverse_image_check(req.image_hash)


@router.post("/fact-check")
async def fact_check(req: TextReq):
    from backend.services.provenance import get_fact_check
    return get_fact_check(req.text)


# --- 2. Claim Extraction ---

@router.post("/claims/extract")
async def extract_claims(req: TextReq):
    from backend.services.claim_extraction import extract_claims
    return extract_claims(req.text)


@router.post("/claims/match")
async def match_evidence(req: TextReq):
    from backend.services.claim_extraction import match_evidence
    return match_evidence(req.text)


# --- 3. Review Workflow ---

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


@router.get("/review/list")
async def list_workflows():
    from backend.services.review_workflow import list_workflows
    return {"workflows": list_workflows()}


# --- 4. Timeline ---

@router.post("/timeline/event")
async def add_timeline_event(content_id: str, event_type: str, source: str):
    from backend.services.timeline_service import add_event
    return add_event(content_id, event_type, source)


@router.get("/timeline/{content_id}")
async def get_timeline(content_id: str):
    from backend.services.timeline_service import get_timeline
    return get_timeline(content_id)


# --- 5. Explainability ---

@router.post("/explain")
async def explain_decision(req: ExplainReq):
    from backend.services.explainability import explain
    return explain(req.modality, req.prediction)


# --- 6. Contradiction Engine ---

@router.post("/contradictions")
async def analyze_contradictions(req: ContradictionReq):
    from backend.services.contradiction_engine import analyze_contradictions
    return analyze_contradictions(req.analysis_results, req.metadata)


# --- 7. Calibration Dashboard ---

@router.get("/calibration/dashboard")
async def get_dashboard():
    from backend.services.calibration_dashboard import get_dashboard
    return get_dashboard()


@router.get("/calibration/modalities")
async def get_modality_performance():
    from backend.services.calibration_dashboard import get_modality_performance
    return get_modality_performance()


# --- 8. Benchmark Dataset ---

@router.get("/benchmark/datasets")
async def list_datasets():
    from backend.services.benchmark_service import get_datasets
    return get_datasets()


@router.get("/benchmark/samples/{modality}")
async def get_samples(modality: str):
    from backend.services.benchmark_service import get_samples
    return {"modality": modality, "samples": get_samples(modality)}


@router.post("/benchmark/evaluate")
async def evaluate_benchmark(req: BenchmarkEvalReq):
    from backend.services.benchmark_service import evaluate_predictions
    return evaluate_predictions(req.modality, req.predictions)


@router.get("/benchmark/metrics")
async def get_benchmark_metrics():
    from backend.services.benchmark_service import get_modality_metrics
    return get_modality_metrics()


@router.get("/benchmark/summary")
async def get_benchmark_summary():
    from backend.services.calibration_dashboard import get_dashboard
    return get_dashboard()["benchmark_results"]
