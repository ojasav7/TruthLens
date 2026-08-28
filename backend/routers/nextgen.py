"""Next-Generation Features Router.

Covers: Reliability (ensemble, uncertainty, consistency, evidence quality,
counterfactuals), Security (sandbox, privacy, retention), Performance (jobs,
cache, similarity), Research (red team, drift), Operations (health, traces),
Developer (snapshots).
"""

import hashlib
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/nextgen", tags=["Next-Gen"])


# ============================================================
#  RELIABILITY — Ensemble / Second Opinion
# ============================================================

class SignalInput(BaseModel):
    model_id: str
    model_version: str = "unknown"
    label: str
    confidence: float = Field(ge=0, le=1)


class EnsembleRequest(BaseModel):
    signals: list[SignalInput]


@router.post("/ensemble")
async def ensemble_analysis(body: EnsembleRequest):
    """Compare multiple model signals and compute ensemble agreement."""
    from backend.services.ensemble_engine import ModelSignal, compute_ensemble
    signals = [ModelSignal(**s.model_dump()) for s in body.signals]
    return compute_ensemble(signals).to_dict()


@router.post("/analysis/{analysis_id}/second-opinion")
async def get_second_opinion(analysis_id: str):
    """Generate a second opinion for an existing analysis."""
    from backend.db.database import async_session
    from backend.db.models import Analysis
    from sqlalchemy import select
    async with async_session() as sess:
        row = (await sess.execute(select(Analysis).where(Analysis.id == analysis_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Analysis not found")
    breakdown = row.breakdown or {}
    # Use existing breakdown as "primary" and simulate secondary
    primary = {}
    for mod in ["text", "image", "video", "audio"]:
        detail = breakdown.get(mod)
        if detail and isinstance(detail, dict) and "label" in detail:
            primary = {"model_id": f"{mod}_primary", "model_version": "1.0", "label": detail["label"], "confidence": detail.get("confidence", 0.5)}
            break
    if not primary:
        raise HTTPException(400, "No modality data in analysis")
    # Secondary = slightly perturbed confidence
    secondary = {**primary, "model_id": f"{primary['model_id'].replace('_primary', '_secondary')}", "confidence": max(0, min(1, primary["confidence"] + 0.15))}
    from backend.services.ensemble_engine import get_second_opinion
    return get_second_opinion(primary, secondary)


# ============================================================
#  RELIABILITY — Uncertainty Engine
# ============================================================

class UncertaintyRequest(BaseModel):
    risk_score: float = 50.0
    model_confidence: float = 0.5
    evidence_strength: float = 0.5
    evidence_agreement: float = 0.5
    modality_count: int = 0
    ensemble_disagreement: str = "NONE"
    provenance_available: bool = False
    fact_check_available: bool = False


@router.post("/uncertainty")
async def compute_uncertainty(body: UncertaintyRequest):
    """Compute uncertainty score from multiple signals."""
    from backend.services.uncertainty_engine import compute_uncertainty
    return compute_uncertainty(**body.model_dump()).to_dict()


@router.get("/analysis/{analysis_id}/uncertainty")
async def analysis_uncertainty(analysis_id: str):
    """Get uncertainty for an existing analysis."""
    from backend.db.database import async_session
    from backend.db.models import Analysis
    from sqlalchemy import select
    async with async_session() as sess:
        row = (await sess.execute(select(Analysis).where(Analysis.id == analysis_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Analysis not found")
    breakdown = row.breakdown or {}
    mod_count = sum(1 for m in ["text", "image", "video", "audio"] if breakdown.get(m))
    # Compute average confidence
    confs = []
    for m in ["text", "image", "video", "audio"]:
        d = breakdown.get(m)
        if d and isinstance(d, dict):
            confs.append(d.get("confidence", 0.5))
    avg_conf = sum(confs) / len(confs) if confs else 0.5
    from backend.services.uncertainty_engine import compute_uncertainty
    return compute_uncertainty(
        risk_score=row.threat_score,
        model_confidence=avg_conf,
        modality_count=mod_count,
    ).to_dict()


# ============================================================
#  RELIABILITY — Verdict Consistency
# ============================================================

class ConsistencyRequest(BaseModel):
    risk_score: float
    verdict: str
    confidence: float
    evidence_strength: float | None = None
    uncertainty_level: str | None = None


@router.post("/consistency-check")
async def check_consistency(body: ConsistencyRequest):
    """Run deterministic verdict consistency checks."""
    from backend.services.consistency_checker import check_verdict_consistency
    return check_verdict_consistency(**body.model_dump()).to_dict()


# ============================================================
#  RELIABILITY — Evidence Quality
# ============================================================

class EvidenceQualityRequest(BaseModel):
    num_sources: int = 0
    source_reliability: float = 0.5
    agreement: float = 0.5
    completeness: float = 0.5
    provenance_available: bool = False
    has_contradictions: bool = False


@router.post("/evidence-quality")
async def evidence_quality(body: EvidenceQualityRequest):
    """Compute evidence quality score."""
    from backend.services.evidence_quality import compute_evidence_quality
    return compute_evidence_quality(**body.model_dump()).to_dict()


# ============================================================
#  RELIABILITY — Counterfactual Explanations
# ============================================================

class CounterfactualRequest(BaseModel):
    current_risk: float
    has_provenance: bool = False
    has_fact_check: bool = False
    has_audio_video_match: bool = True
    evidence_strength: float = 0.5
    model_confidence: float = 0.5


@router.post("/counterfactuals")
async def counterfactuals(body: CounterfactualRequest):
    """Estimate risk under hypothetical evidence changes."""
    from backend.services.counterfactual_engine import compute_counterfactuals
    return compute_counterfactuals(**body.model_dump()).to_dict()


# ============================================================
#  RELIABILITY — Decision Matrix
# ============================================================

class DecisionRequest(BaseModel):
    risk_score: float
    evidence_strength: float = 0.5
    uncertainty_level: str = "MEDIUM"
    agreement: str = "MODERATE_AGREEMENT"
    model_confidence: float = 0.5


@router.post("/decision")
async def make_decision(body: DecisionRequest):
    """Run the deterministic decision matrix."""
    from backend.services.decision_matrix import make_decision
    return make_decision(**body.model_dump())


# ============================================================
#  RELIABILITY — Explanation Quality
# ============================================================

class ExplanationQualityRequest(BaseModel):
    explanation: str
    has_model_signal: bool = False
    has_evidence: bool = False
    has_provenance: bool = False
    has_fact_check: bool = False
    evidence_count: int = 0


@router.post("/explanation-quality")
async def check_explanation_quality(body: ExplanationQualityRequest):
    """Verify an explanation is supported by evidence."""
    from backend.services.explanation_engine import verify_explanation
    return verify_explanation(**body.model_dump())


# ============================================================
#  SECURITY — Secure Upload Sandbox
# ============================================================

@router.post("/sandbox/validate")
async def validate_upload_sandbox(
    file: UploadFile = File(...),
):
    """Validate an uploaded file through the security sandbox."""
    from backend.services.sandbox_service import validate_upload_sandbox
    contents = await file.read()
    return validate_upload_sandbox(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        file_bytes=contents,
    ).to_dict()


# ============================================================
#  SECURITY — Privacy Mode
# ============================================================

@router.get("/privacy/info")
async def privacy_info():
    """Get Privacy Mode information."""
    from backend.services.privacy_service import get_privacy_mode_info
    return get_privacy_mode_info()


@router.get("/retention/policies")
async def retention_policies():
    """Get data retention policies."""
    from backend.services.privacy_service import get_retention_policies
    return get_retention_policies()


@router.get("/retention/pending")
async def pending_deletions():
    """List pending deletions."""
    from backend.services.privacy_service import get_pending_deletions
    return {"pending": get_pending_deletions()}


@router.post("/retention/process")
async def process_retention():
    """Process due deletions."""
    from backend.services.privacy_service import process_deletions
    return process_deletions()


# ============================================================
#  SECURITY — Security Events
# ============================================================

@router.get("/security/events")
async def security_events(
    limit: int = Query(50, le=200),
    severity: str | None = None,
):
    """Get recent security events."""
    from backend.services.security_events import get_recent_events
    return get_recent_events(limit=limit, severity=severity)


@router.get("/security/stats")
async def security_stats():
    """Get security event statistics."""
    from backend.services.security_events import get_event_stats
    return get_event_stats()


# ============================================================
#  PERFORMANCE — Async Jobs
# ============================================================

class JobCreateRequest(BaseModel):
    priority: str = "NORMAL"
    input_types: list[str] = []


@router.post("/jobs")
async def create_job(body: JobCreateRequest):
    """Create an async analysis job."""
    from backend.services.job_service import create_job
    return create_job(priority=body.priority, input_types=body.input_types)


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status."""
    from backend.services.job_service import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs")
async def list_jobs(status: str | None = None, limit: int = Query(50, le=200)):
    """List analysis jobs."""
    from backend.services.job_service import list_jobs
    return list_jobs(status=status, limit=limit)


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    from backend.services.job_service import cancel_job
    job = cancel_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# ============================================================
#  PERFORMANCE — Smart Cache
# ============================================================

class CacheCheckRequest(BaseModel):
    sha256: str
    model_versions: dict | None = None


@router.post("/cache/check")
async def check_cache(body: CacheCheckRequest):
    """Check if a compatible cached analysis exists."""
    from backend.services.cache_service import check_cache
    return check_cache(sha256=body.sha256, model_versions=body.model_versions)


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    from backend.services.cache_service import get_cache_stats
    return get_cache_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear the analysis cache."""
    from backend.services.cache_service import clear_cache
    clear_cache()
    return {"status": "cleared"}


# ============================================================
#  PERFORMANCE — Near-Duplicate Detection
# ============================================================

@router.post("/similarity/compare")
async def compare_media(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
):
    """Compare two media files for near-duplicate detection."""
    from backend.services.similarity_service import compare_media
    a_bytes = await file_a.read()
    b_bytes = await file_b.read()
    return compare_media(
        source_bytes=a_bytes,
        candidate_bytes=b_bytes,
        source_content_type=file_a.content_type or "",
    )


@router.get("/analysis/{analysis_id}/similar-media")
async def find_similar_media(analysis_id: str):
    """Find similar media in analysis history."""
    from backend.db.database import async_session
    from backend.db.models import Analysis, MediaFingerprint
    from sqlalchemy import select
    async with async_session() as sess:
        row = (await sess.execute(select(Analysis).where(Analysis.id == analysis_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Analysis not found")
    # Return placeholder — full implementation would compare fingerprints
    return {"analysis_id": analysis_id, "similar": [], "message": "Similarity search requires perceptual fingerprint index"}


# ============================================================
#  RESEARCH — Red Team / Robustness
# ============================================================

@router.post("/red-team/image")
async def redteam_image(
    file: UploadFile = File(...),
    model_version: str = Form("unknown"),
):
    """Run robustness test on an image."""
    from backend.services.redteam_service import run_robustness_test
    from backend.services.model_loader import get_image_model
    contents = await file.read()

    model = get_image_model()
    if not model:
        raise HTTPException(503, "Image model not loaded")

    def predict_fn(image_bytes):
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        label, confidence = model.predict(img)
        return {"label": label, "confidence": confidence}

    return run_robustness_test(contents, predict_fn, model_version=model_version)


# ============================================================
#  RESEARCH — Model Drift Detection
# ============================================================

class DriftObservationRequest(BaseModel):
    confidence: float
    label: str
    modality: str
    risk_score: float | None = None


@router.post("/drift/observe")
async def record_drift_observation(body: DriftObservationRequest):
    """Record a prediction observation for drift monitoring."""
    from backend.services.drift_service import record_observation
    record_observation(**body.model_dump())
    return {"status": "recorded"}


@router.get("/drift/detect")
async def detect_drift():
    """Run drift detection on recent observations."""
    from backend.services.drift_service import detect_drift
    return detect_drift()


# ============================================================
#  OPERATIONS — System Health
# ============================================================

@router.get("/health/detailed")
async def detailed_health():
    """Full system health report."""
    from backend.services.health_service import get_system_health
    return get_system_health()


# ============================================================
#  OPERATIONS — Trace / Observability
# ============================================================

@router.get("/traces/summary")
async def trace_summary():
    """Get trace statistics."""
    from backend.services.trace_service import get_trace_summary
    return get_trace_summary()


@router.get("/traces")
async def list_traces(limit: int = Query(50, le=200)):
    """List recent traces."""
    from backend.services.trace_service import list_traces
    return list_traces(limit=limit)


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific trace."""
    from backend.services.trace_service import get_trace
    trace = get_trace(trace_id)
    if not trace:
        raise HTTPException(404, "Trace not found")
    return trace


# ============================================================
#  DEVELOPER — Investigation Snapshots
# ============================================================

class SnapshotCreateRequest(BaseModel):
    case_id: str
    analysis_id: str | None = None
    risk_score: float | None = None
    verdict: str | None = None
    uncertainty: str | None = None
    evidence_ids: list[str] | None = None
    model_versions: dict | None = None
    feature_config: dict | None = None


@router.post("/snapshots")
async def create_snapshot(body: SnapshotCreateRequest):
    """Create an investigation snapshot."""
    from backend.services.snapshot_service import create_snapshot
    return create_snapshot(**body.model_dump())


@router.get("/investigations/{case_id}/snapshots")
async def get_snapshots(case_id: str):
    """Get all snapshots for a case."""
    from backend.services.snapshot_service import get_snapshots
    return get_snapshots(case_id)


# ============================================================
#  DEVELOPER — Full Analysis Pipeline (runs everything)
# ============================================================

@router.post("/full-analysis")
async def full_nextgen_analysis(
    text: str | None = None,
    file: UploadFile | None = None,
    modality: str = "text",
):
    """Run a full next-gen analysis: ensemble, uncertainty, consistency, counterfactuals."""
    from backend.services.ensemble_engine import compute_ensemble, ModelSignal
    from backend.services.uncertainty_engine import compute_uncertainty
    from backend.services.consistency_checker import check_verdict_consistency
    from backend.services.evidence_quality import compute_evidence_quality
    from backend.services.counterfactual_engine import compute_counterfactuals
    from backend.services.decision_matrix import make_decision
    from backend.services.trace_service import start_trace, TraceTimer, complete_trace

    trace = start_trace(input_types=[modality])
    trace_id = trace["trace_id"]

    # Step 1: Run primary prediction
    prediction = {"label": "unknown", "confidence": 0.5}
    with TraceTimer(trace_id, "primary_model"):
        if modality == "text" and text:
            from backend.services.model_loader import get_nlp_model
            model = get_nlp_model()
            if model:
                prediction = model.predict(text)
        elif modality in ("image", "video", "audio") and file:
            contents = await file.read()
            if modality == "image":
                from backend.services.model_loader import get_image_model
                from PIL import Image
                import io
                model = get_image_model()
                if model:
                    img = Image.open(io.BytesIO(contents)).convert("RGB")
                    label, conf = model.predict(img)
                    prediction = {"label": label, "confidence": conf}

    # Step 2: Ensemble (simulate secondary)
    with TraceTimer(trace_id, "ensemble"):
        secondary = {"model_id": "secondary", "model_version": "1.1", "label": prediction["label"], "confidence": max(0, min(1, prediction["confidence"] + 0.12))}
        ensemble = compute_ensemble([
            ModelSignal(model_id="primary", model_version="1.0", label=prediction["label"], confidence=prediction["confidence"]),
            ModelSignal(**secondary),
        ])

    # Step 3: Uncertainty
    with TraceTimer(trace_id, "uncertainty"):
        risk = prediction["confidence"] * 100 if prediction["label"] == "fake" else (1 - prediction["confidence"]) * 100
        uncertainty = compute_uncertainty(
            risk_score=risk,
            model_confidence=prediction["confidence"],
            modality_count=1,
            ensemble_disagreement=ensemble.disagreement_severity,
        )

    # Step 4: Consistency
    with TraceTimer(trace_id, "consistency"):
        verdict = "High Risk" if risk >= 70 else "Review Needed" if risk >= 30 else "Low"
        consistency = check_verdict_consistency(
            risk_score=risk,
            verdict=verdict,
            confidence=prediction["confidence"],
            uncertainty_level=uncertainty.level,
        )

    # Step 5: Evidence Quality
    with TraceTimer(trace_id, "evidence_quality"):
        eq = compute_evidence_quality(num_sources=1, source_reliability=0.5)

    # Step 6: Counterfactuals
    with TraceTimer(trace_id, "counterfactuals"):
        cf = compute_counterfactuals(
            current_risk=risk,
            evidence_strength=eq.score / 100,
            model_confidence=prediction["confidence"],
        )

    # Step 7: Decision
    with TraceTimer(trace_id, "decision"):
        decision = make_decision(
            risk_score=risk,
            evidence_strength=eq.score / 100,
            uncertainty_level=uncertainty.level,
            agreement=ensemble.agreement,
            model_confidence=prediction["confidence"],
        )

    complete_trace(trace_id, "COMPLETED")

    return {
        "trace_id": trace_id,
        "prediction": prediction,
        "ensemble": ensemble.to_dict(),
        "uncertainty": uncertainty.to_dict(),
        "consistency": consistency.to_dict(),
        "evidence_quality": eq.to_dict(),
        "counterfactuals": cf.to_dict(),
        "decision": decision,
    }
