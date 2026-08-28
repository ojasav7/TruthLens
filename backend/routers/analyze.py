"""
Analysis router — multimodal analysis with trace IDs, security events, metrics.
"""

import io
import os
import time
import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from slowapi import Limiter

from backend.services.model_loader import (
    get_nlp_model,
    get_image_model,
    get_video_model,
    get_audio_model,
)
from backend.services.sandbox_service import validate_upload_sandbox as validate_upload
from backend.services.security_events import record_event
from backend.services.trace_service import start_trace, complete_trace
from backend.services.prometheus_metrics import record_analysis
from backend.services.drift_service import record_observation

router = APIRouter()
limiter = Limiter(key_func=lambda request: "global")


def validate_text(text: str) -> str:
    """Validate and sanitize text input."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    text = text.strip()
    if len(text) > 10000:
        raise HTTPException(status_code=400, detail="Text too long (max 10,000 chars)")
    return text


# ============================================================
# ANALYSIS RESPONSE MODEL
# ============================================================

from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    id: str
    timestamp: str
    threat_score: float
    verdict: str
    consistency: str
    breakdown: dict
    trace_id: str | None = None
    input_types: list[str] = []


# ============================================================
# MAIN ANALYSIS ENDPOINT
# ============================================================

@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("30/minute")
async def analyze(request: Request,
    text: str | None = Form(None),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
):
    """
    Combined multimodal analysis.
    Accepts any subset of text/image/video/audio, at least one required.
    Generates trace ID, logs security events, records metrics.
    """
    t_start = time.time()
    trace_info = start_trace()
    trace_id = trace_info["trace_id"]

    # Normalize: strip whitespace, treat empty string as None
    if text:
        text = text.strip() or None

    # Validate at least one input
    if not text and not image and not video and not audio:
        record_event("empty_analysis_request", severity="WARNING", details={"ip": request.client.host if request.client else "unknown"})
        raise HTTPException(
            status_code=400,
            detail="At least one input (text, image, video, audio) is required",
        )

    scores = {"text": None, "image": None, "video": None, "audio": None}
    input_types = []
    module_timings = {}

    nlp = get_nlp_model()
    img_model = get_image_model()
    vid_model = get_video_model()
    aud_model = get_audio_model()

    # --- NLP ---
    if text and nlp:
        t_mod = time.time()
        text = validate_text(text)
        scores["text"] = nlp.predict(text)
        input_types.append("text")
        module_timings["nlp"] = round((time.time() - t_mod) * 1000, 1)

    # --- Image ---
    if image and img_model:
        t_mod = time.time()
        try:
            contents = await image.read()
            # Validate in sandbox
            vr = validate_upload_sandbox(image.filename or "image.jpg", image.content_type, contents)
            if not vr.valid:
                err_msg = "; ".join(vr.errors) if vr.errors else "validation failed"
                record_event("unsafe_upload_rejected", severity="WARNING", details={"filename": image.filename, "reason": err_msg})
                scores["image"] = {"label": "error", "confidence": 0.0, "error": f"Upload rejected: {err_msg}"}
            else:
                pil_img = __import__("PIL").Image.open(io.BytesIO(contents)).convert("RGB")
                scores["image"] = img_model.predict(pil_img)
                input_types.append("image")
                module_timings["image"] = round((time.time() - t_mod) * 1000, 1)
        except Exception as e:
            record_event("image_analysis_error", severity="ERROR", details={"error": str(e), "filename": image.filename})
            scores["image"] = {"label": "error", "confidence": 0.0, "error": str(e)}

    # --- Video ---
    if video and vid_model:
        t_mod = time.time()
        try:
            contents = await video.read()
            vr = validate_upload_sandbox(video.filename or "video.mp4", video.content_type, contents)
            if not vr.valid:
                err_msg = "; ".join(vr.errors) if vr.errors else "validation failed"
                record_event("unsafe_upload_rejected", severity="WARNING", details={"filename": video.filename, "reason": err_msg})
                scores["video"] = {"label": "error", "confidence": 0.0, "error": f"Upload rejected: {err_msg}"}
            else:
                suffix = Path(video.filename or "video.mp4").suffix or ".mp4"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(contents)
                    tmp_path = tmp.name
                try:
                    scores["video"] = vid_model.predict(tmp_path)
                    input_types.append("video")
                    module_timings["video"] = round((time.time() - t_mod) * 1000, 1)
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
        except Exception as e:
            record_event("video_analysis_error", severity="ERROR", details={"error": str(e), "filename": video.filename})
            scores["video"] = {"label": "error", "confidence": 0.0, "error": str(e)}

    # --- Audio ---
    if audio and aud_model:
        t_mod = time.time()
        try:
            contents = await audio.read()
            vr = validate_upload_sandbox(audio.filename or "audio.wav", audio.content_type, contents)
            if not vr.valid:
                err_msg = "; ".join(vr.errors) if vr.errors else "validation failed"
                record_event("unsafe_upload_rejected", severity="WARNING", details={"filename": audio.filename, "reason": err_msg})
                scores["audio"] = {"label": "error", "confidence": 0.0, "error": f"Upload rejected: {err_msg}"}
            else:
                suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(contents)
                    tmp_path = tmp.name
                try:
                    scores["audio"] = aud_model.predict(tmp_path)
                    input_types.append("audio")
                    module_timings["audio"] = round((time.time() - t_mod) * 1000, 1)
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
        except Exception as e:
            record_event("audio_analysis_error", severity="ERROR", details={"error": str(e), "filename": audio.filename})
            scores["audio"] = {"label": "error", "confidence": 0.0, "error": str(e)}

    # --- Fusion ---
    from models.fusion.fuse import fuse
    fused = fuse(scores)

    # --- Store to DB ---
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

    from backend.db.database import async_session
    from backend.db.models import Analysis

    async with async_session() as session:
        record = Analysis(
            id=analysis_id,
            timestamp=timestamp,
            input_types=input_types,
            threat_score=fused["threat_score"],
            verdict=fused["verdict"],
            breakdown=fused["breakdown"],
        )
        session.add(record)
        await session.commit()

    # --- Record metrics & observations ---
    duration_ms = round((time.time() - t_start) * 1000, 1)
    for mod in input_types:
        record_analysis(mod, fused["verdict"])
    for mod in input_types:
        detail = fused["breakdown"].get(mod)
        if detail and isinstance(detail, dict):
            record_observation(
                confidence=detail.get("confidence", 0),
                label=detail.get("label", "unknown"),
                modality=mod,
                risk_score=fused["threat_score"],
            )

    # Complete trace
    complete_trace(trace_id, "COMPLETED")

    # Log successful analysis
    record_event("analysis_complete", severity="INFO", details={
        "analysis_id": analysis_id,
        "verdict": fused["verdict"],
        "score": fused["threat_score"],
        "duration_ms": duration_ms,
    })

    return AnalysisResponse(
        id=analysis_id,
        timestamp=timestamp.isoformat(),
        threat_score=fused["threat_score"],
        verdict=fused["verdict"],
        consistency=fused.get("consistency", "unanimous"),
        breakdown=fused["breakdown"],
        trace_id=trace_id,
        input_types=input_types,
    )


# ============================================================
# LIST ANALYSES
# ============================================================

@router.get("/analyses")
async def list_analyses(
    limit: int = 20,
    verdict: str | None = None,
    min_risk: float | None = None,
    max_risk: float | None = None,
    input_type: str | None = None,
):
    """List recent analyses with optional filters."""
    from backend.db.database import async_session
    from backend.db.models import Analysis
    from sqlalchemy import select, desc

    async with async_session() as session:
        query = select(Analysis).order_by(desc(Analysis.timestamp)).limit(limit)
        if verdict:
            query = query.where(Analysis.verdict == verdict)
        if min_risk is not None:
            query = query.where(Analysis.threat_score >= min_risk)
        if max_risk is not None:
            query = query.where(Analysis.threat_score <= max_risk)

        result = await session.execute(query)
        rows = result.scalars().all()

        if input_type:
            rows = [r for r in rows if input_type in (r.input_types or [])]

        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "input_types": r.input_types,
                "threat_score": r.threat_score,
                "verdict": r.verdict,
            }
            for r in rows
        ]


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@router.get("/analyze/{analysis_id}/report")
async def download_report(analysis_id: str):
    """Download a PDF report for a completed analysis."""
    from backend.db.database import async_session
    from backend.db.models import Analysis
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
        record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_dict = {
        "id": record.id,
        "timestamp": record.timestamp.isoformat(),
        "input_types": record.input_types,
        "threat_score": record.threat_score,
        "verdict": record.verdict,
        "breakdown": record.breakdown,
    }

    from backend.services.report_service import generate_report
    pdf_path = generate_report(analysis_dict)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"truthlens_report_{analysis_id[:8]}.pdf",
    )
