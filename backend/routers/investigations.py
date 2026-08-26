"""Investigation API — new endpoints that don't touch existing /analyze."""

from fastapi import APIRouter, HTTPException, Query
from backend.services.investigation_service import InvestigationService
from backend.services.audit_service import AuditService
from backend.services.contradiction_engine import ContradictionEngine
from backend.services.video_timeline import analyze_timeline
from backend.services.explanation_engine import generate_explanation

router = APIRouter(prefix="/investigations", tags=["Investigations"])
inv_service = InvestigationService()
audit_service = AuditService()
contradiction_engine = ContradictionEngine()


@router.post("/{analysis_id}")
async def create_investigation(analysis_id: str):
    """Create an investigation from an existing analysis."""
    result = await inv_service.create_from_analysis(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{case_id}")
async def get_investigation(case_id: str):
    """Get full investigation with evidence, contradiction analysis, and audit trail."""
    result = await inv_service.get_investigation(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Add contradiction analysis if multiple modalities present
    evidence_sources = {e["type"].split("_")[0].lower() for e in result.get("evidence", [])}
    breakdown = {}
    for ev in result.get("evidence", []):
        modality = ev["type"].split("_")[0].lower()
        breakdown[modality] = {"label": "fake" if ev["category"] == "SUPPORTING" else "real", "confidence": ev.get("score", 0.5)}

    contradiction = contradiction_engine.analyze(breakdown) if len(breakdown) >= 2 else None
    result["cross_modal_analysis"] = contradiction

    # Add explanation
    result["explanation"] = generate_explanation(result, contradiction)

    return result


@router.get("/{case_id}/audit")
async def get_audit_trail(case_id: str):
    """Get chronological audit events for a case."""
    timeline = await audit_service.get_timeline(case_id)
    return {"case_id": case_id, "events": timeline}


@router.get("/{case_id}/timeline")
async def get_video_timeline(case_id: str):
    """Get video temporal timeline for an investigation."""
    result = await inv_service.get_investigation(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Find video evidence with per_frame_scores in metadata
    for ev in result.get("evidence", []):
        meta = ev.get("metadata_json") or {}
        if "per_frame_scores" in meta:
            return analyze_timeline(meta["per_frame_scores"])

    return {"segments": [], "total_frames": 0, "message": "No video data available"}


@router.post("/{case_id}/reanalyze")
async def reanalyze(case_id: str):
    """Re-analyze a case — creates a new version without overwriting the old."""
    result = await inv_service.get_investigation(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    analysis_ids = result.get("analysis_ids", []) if "analysis_ids" in result else []
    if not analysis_ids:
        # Fallback: try to get from the case directly
        from backend.db.database import async_session
        from backend.db.models_advanced import InvestigationCase
        from sqlalchemy import select
        async with async_session() as session:
            r = await session.execute(select(InvestigationCase).where(InvestigationCase.id == case_id))
            case = r.scalar_one_or_none()
            if case:
                analysis_ids = case.analysis_ids or []

    if not analysis_ids:
        raise HTTPException(status_code=400, detail="No analysis IDs found for re-analysis")

    # Create new investigation from the latest analysis
    new_result = await inv_service.create_from_analysis(analysis_ids[-1])
    if "error" in new_result:
        raise HTTPException(status_code=500, detail=new_result["error"])

    await audit_service.log(case_id, "REANALYSIS_COMPLETED", {"new_case_id": new_result["case_id"]})
    return {"original_case_id": case_id, "new_case_id": new_result["case_id"], "risk_score": new_result["risk_score"]}
