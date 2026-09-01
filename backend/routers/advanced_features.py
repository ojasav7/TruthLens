"""
Advanced Features Router
API endpoints for all 8 advanced features:
1. Source verification & provenance chain
2. Claim extraction and evidence matching
3. Human-in-the-loop review workflow
4. Timeline + narrative investigation view
5. Explainability beyond model internals
6. Cross-modal contradiction engine
7. Model calibration and benchmarking dashboard
8. Real-world dataset / benchmark layer
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from backend.services.source_verification import get_source_verifier
from backend.services.claim_extraction import get_claim_extractor
from backend.services.review_workflow import get_review_manager
from backend.services.timeline_service import get_timeline_service
from backend.services.explainability import get_explainability_service
from backend.services.contradiction_engine import get_contradiction_engine
from backend.services.calibration_dashboard import get_calibration_dashboard
from backend.services.benchmark_dataset import get_benchmark_service


router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# ============================================================
# Request Models
# ============================================================

class SourceVerifyRequest(BaseModel):
    url: str
    content_text: Optional[str] = None
    image_hash: Optional[str] = None


class ClaimCheckRequest(BaseModel):
    claim: str
    context: Optional[str] = None


class ReviewAssignRequest(BaseModel):
    analysis_id: str
    reviewer_id: str


class ReviewCommentRequest(BaseModel):
    analysis_id: str
    reviewer_id: str
    comment: str
    comment_type: str = "general"


class VerdictOverrideRequest(BaseModel):
    analysis_id: str
    reviewer_id: str
    new_verdict: str
    reason: str


class DispositionRequest(BaseModel):
    analysis_id: str
    reviewer_id: str
    disposition: str
    notes: str = ""


class TimelineEventRequest(BaseModel):
    investigation_id: str
    event_type: str
    source: str
    platform: Optional[str] = None
    url: Optional[str] = None
    details: dict = {}


class ExplainRequest(BaseModel):
    modality: str
    prediction: dict
    input_data: Optional[dict] = None


class ContradictionRequest(BaseModel):
    analysis_results: dict
    content_metadata: Optional[dict] = None


class BenchmarkEvaluateRequest(BaseModel):
    dataset_id: str
    model_name: str
    predictions: list


# ============================================================
# Feature 1: Source Verification & Provenance Chain
# ============================================================

@router.post("/source-verify/verify")
async def verify_source(request: SourceVerifyRequest):
    """Verify a source URL for credibility and provenance."""
    verifier = get_source_verifier()
    
    try:
        result = verifier.verify_source(request.url)
        
        if request.content_text:
            fact_checks = verifier.check_fact_database(request.content_text)
            result.fact_check_results = fact_checks
        
        if request.image_hash:
            reverse_results = verifier.reverse_image_search(request.image_hash)
            result.reverse_image_results = reverse_results
        
        return {"status": "success", "data": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/source-verify/check-claim")
async def check_claim(request: ClaimCheckRequest):
    """Check a claim against fact-check databases."""
    verifier = get_source_verifier()
    
    try:
        results = verifier.check_fact_database(request.claim)
        return {"status": "success", "data": {"claim": request.claim, "results": results}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim check failed: {str(e)}")


@router.get("/source-verify/provenance/{url:path}")
async def get_provenance_chain(url: str):
    """Get provenance chain for a URL."""
    verifier = get_source_verifier()
    
    try:
        chain = verifier.build_provenance_chain(url)
        return {"status": "success", "data": {"url": url, "chain": chain}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provenance check failed: {str(e)}")


# ============================================================
# Feature 2: Claim Extraction & Evidence Matching
# ============================================================

@router.post("/claims/extract")
async def extract_claims(text: str):
    """Extract claims from text."""
    extractor = get_claim_extractor()
    
    try:
        result = extractor.extract_claims(text)
        return {"status": "success", "data": {
            "claims": result.claims,
            "total_claims": result.total_claims,
            "verified_claims": result.verified_claims,
            "contradicted_claims": result.contradicted_claims,
            "confidence": result.confidence,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.post("/claims/match")
async def match_evidence(claim: str):
    """Match a claim to known evidence."""
    extractor = get_claim_extractor()
    
    try:
        result = extractor.match_evidence(claim)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence matching failed: {str(e)}")


@router.post("/claims/compare-media")
async def compare_media_caption(caption: str, media_analysis: dict):
    """Compare media caption with actual media content analysis."""
    extractor = get_claim_extractor()
    
    try:
        result = extractor.compare_media_caption(caption, media_analysis)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Media comparison failed: {str(e)}")


# ============================================================
# Feature 3: Human-in-the-Loop Review Workflow
# ============================================================

@router.post("/review/assign")
async def assign_reviewer(request: ReviewAssignRequest):
    """Assign a reviewer to an analysis."""
    manager = get_review_manager()
    
    try:
        workflow = manager.assign_reviewer(request.analysis_id, request.reviewer_id)
        return {"status": "success", "data": manager._workflow_to_dict(workflow)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")


@router.post("/review/comment")
async def add_comment(request: ReviewCommentRequest):
    """Add a reviewer comment."""
    manager = get_review_manager()
    
    try:
        workflow = manager.add_comment(
            request.analysis_id, request.reviewer_id, request.comment, request.comment_type
        )
        return {"status": "success", "data": manager._workflow_to_dict(workflow)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comment failed: {str(e)}")


@router.post("/review/override-verdict")
async def override_verdict(request: VerdictOverrideRequest):
    """Override the AI verdict with human judgment."""
    manager = get_review_manager()
    
    try:
        workflow = manager.override_verdict(
            request.analysis_id, request.reviewer_id, request.new_verdict, request.reason
        )
        return {"status": "success", "data": manager._workflow_to_dict(workflow)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")


@router.post("/review/set-disposition")
async def set_disposition(request: DispositionRequest):
    """Set final case disposition."""
    manager = get_review_manager()
    
    try:
        workflow = manager.set_disposition(
            request.analysis_id, request.reviewer_id, request.disposition, request.notes
        )
        return {"status": "success", "data": manager._workflow_to_dict(workflow)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disposition failed: {str(e)}")


@router.get("/review/audit-trail/{analysis_id}")
async def get_audit_trail(analysis_id: str):
    """Get audit trail for an analysis."""
    manager = get_review_manager()
    
    try:
        trail = manager.get_audit_trail(analysis_id)
        return {"status": "success", "data": {"analysis_id": analysis_id, "audit_trail": trail}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit trail failed: {str(e)}")


# ============================================================
# Feature 4: Timeline & Narrative Investigation View
# ============================================================

@router.post("/timeline/create")
async def create_investigation(content_id: str):
    """Create a new narrative investigation."""
    service = get_timeline_service()
    
    try:
        investigation = service.create_investigation(content_id)
        return {"status": "success", "data": {
            "content_id": investigation.content_id,
            "created_at": investigation.created_at,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation creation failed: {str(e)}")


@router.post("/timeline/add-event")
async def add_timeline_event(request: TimelineEventRequest):
    """Add an event to the investigation timeline."""
    service = get_timeline_service()
    
    try:
        investigation = service.create_investigation(request.investigation_id)
        
        if request.event_type == "publication":
            investigation = service.add_publication_event(
                investigation, request.source, request.platform or "unknown", request.url
            )
        elif request.event_type == "share":
            investigation = service.add_share_event(
                investigation, request.source, request.platform or "unknown", request.url
            )
        elif request.event_type == "edit":
            investigation = service.add_edit_event(
                investigation, request.source, "content_change", request.details
            )
        
        return {"status": "success", "data": {
            "content_id": investigation.content_id,
            "timeline": investigation.timeline,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event addition failed: {str(e)}")


@router.get("/timeline/summary/{content_id}")
async def get_timeline_summary(content_id: str):
    """Get timeline summary for an investigation."""
    service = get_timeline_service()
    
    try:
        investigation = service.create_investigation(content_id)
        summary = service.generate_summary(investigation)
        return {"status": "success", "data": {
            "content_id": content_id,
            "summary": summary,
            "timeline": investigation.timeline,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")


# ============================================================
# Feature 5: Explainability Beyond Model Internals
# ============================================================

@router.post("/explain")
async def explain_decision(request: ExplainRequest):
    """Generate human-friendly explanation for a model decision."""
    service = get_explainability_service()
    
    try:
        explanation = service.explain_decision(request.modality, request.prediction, request.input_data)
        return {"status": "success", "data": {
            "summary": explanation.summary,
            "confidence_factors": explanation.confidence_factors,
            "key_indicators": explanation.key_indicators,
            "visual_attention": explanation.visual_attention,
            "feature_importance": explanation.feature_importance,
            "recommendations": explanation.recommendations,
            "technical_details": explanation.technical_details,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/explain/text")
async def explain_text(text: str, prediction: dict):
    """Explain text analysis results."""
    service = get_explainability_service()
    
    try:
        explanation = service.explain_text_analysis(text, prediction)
        return {"status": "success", "data": {
            "summary": explanation.summary,
            "confidence_factors": explanation.confidence_factors,
            "key_indicators": explanation.key_indicators,
            "recommendations": explanation.recommendations,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text explanation failed: {str(e)}")


@router.post("/explain/image")
async def explain_image(image_info: dict, prediction: dict):
    """Explain image analysis results."""
    service = get_explainability_service()
    
    try:
        explanation = service.explain_image_analysis(image_info, prediction)
        return {"status": "success", "data": {
            "summary": explanation.summary,
            "confidence_factors": explanation.confidence_factors,
            "key_indicators": explanation.key_indicators,
            "visual_attention": explanation.visual_attention,
            "feature_importance": explanation.feature_importance,
            "recommendations": explanation.recommendations,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image explanation failed: {str(e)}")


# ============================================================
# Feature 6: Cross-Modal Contradiction Engine
# ============================================================

@router.post("/contradictions/analyze")
async def analyze_contradictions(request: ContradictionRequest):
    """Analyze all modalities for contradictions."""
    engine = get_contradiction_engine()
    
    try:
        result = engine.analyze_contradictions(request.analysis_results, request.content_metadata)
        return {"status": "success", "data": {
            "contradictions": result.contradictions,
            "total_contradictions": result.total_contradictions,
            "critical_contradictions": result.critical_contradictions,
            "consistency_score": result.consistency_score,
            "modalities_analyzed": result.modalities_analyzed,
            "summary": result.summary,
            "recommendations": result.recommendations,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contradiction analysis failed: {str(e)}")


# ============================================================
# Feature 7: Model Calibration & Benchmarking Dashboard
# ============================================================

@router.get("/calibration/dashboard")
async def get_calibration_dashboard_data():
    """Get complete calibration dashboard data."""
    dashboard = get_calibration_dashboard()
    
    try:
        data = dashboard.get_dashboard_data()
        return {"status": "success", "data": {
            "calibration_curve": data.calibration_curve,
            "confidence_distribution": data.confidence_distribution,
            "modality_performance": data.modality_performance,
            "overall_performance": data.overall_performance,
            "false_positive_rate": data.false_positive_rate,
            "false_negative_rate": data.false_negative_rate,
            "benchmark_results": data.benchmark_results,
            "timestamp": data.timestamp,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")


@router.get("/calibration/modality-performance")
async def get_modality_performance():
    """Get per-modality performance metrics."""
    dashboard = get_calibration_dashboard()
    
    try:
        performance = dashboard.get_modality_performance()
        return {"status": "success", "data": performance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")


# ============================================================
# Feature 8: Real-World Dataset & Benchmark Layer
# ============================================================

@router.post("/benchmark/evaluate")
async def evaluate_model(request: BenchmarkEvaluateRequest):
    """Evaluate a model on a benchmark dataset."""
    service = get_benchmark_service()
    
    try:
        report = service.evaluate_model(request.dataset_id, request.model_name, request.predictions)
        return {"status": "success", "data": {
            "report_id": report.report_id,
            "model_name": report.model_name,
            "dataset_name": report.dataset_name,
            "overall_accuracy": report.overall_accuracy,
            "per_class_metrics": report.per_class_metrics,
            "per_category_metrics": report.per_category_metrics,
            "per_difficulty_metrics": report.per_difficulty_metrics,
            "confusion_matrix": report.confusion_matrix,
            "roc_auc": report.roc_auc,
            "average_precision": report.average_precision,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model evaluation failed: {str(e)}")


@router.get("/benchmark/datasets")
async def list_datasets():
    """List all benchmark datasets."""
    service = get_benchmark_service()
    
    try:
        datasets = []
        for dataset_id, data in service.datasets.items():
            dataset = data["dataset"]
            datasets.append({
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "modality": dataset.modality,
                "total_samples": dataset.total_samples,
                "real_samples": dataset.real_samples,
                "fake_samples": dataset.fake_samples,
            })
        return {"status": "success", "data": datasets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset listing failed: {str(e)}")


@router.get("/benchmark/summary")
async def get_benchmark_summary():
    """Get summary of all benchmark evaluations."""
    service = get_benchmark_service()
    
    try:
        summary = service.get_evaluation_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark summary failed: {str(e)}")
