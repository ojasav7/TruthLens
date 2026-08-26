"""Unified multimodal analysis endpoint — Phase 5"""

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.db.database import async_session
from backend.db.models import Analysis
from backend.services.model_loader import get_nlp_model, get_image_model, get_video_model, get_audio_model
from models.fusion.fuse import fuse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class AnalysisResponse(BaseModel):
    id: str
    timestamp: str
    threat_score: float
    verdict: str
    consistency: str
    breakdown: dict


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
    """
    # Validate at least one input
    if not text and not image and not video and not audio:
        raise HTTPException(
            status_code=400,
            detail="At least one input (text, image, video, audio) is required",
        )

    scores = {"text": None, "image": None, "video": None, "audio": None}
    input_types = []

    nlp = get_nlp_model()
    img_model = get_image_model()
    vid_model = get_video_model()
    aud_model = get_audio_model()

    # --- NLP ---
    if text and nlp:
        scores["text"] = nlp.predict(text)
        input_types.append("text")

    # --- Image ---
    if image and img_model:
        try:
            contents = await image.read()
            pil_img = __import__("PIL").Image.open(io.BytesIO(contents)).convert("RGB")
            scores["image"] = img_model.predict(pil_img)
            input_types.append("image")
        except Exception as e:
            scores["image"] = {"label": "error", "confidence": 0.0, "error": str(e)}

    # --- Video ---
    if video and vid_model:
        suffix = Path(video.filename or "video.mp4").suffix or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await video.read()
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            scores["video"] = vid_model.predict(tmp_path)
            input_types.append("video")
        except Exception as e:
            scores["video"] = {"label": "error", "confidence": 0.0, "error": str(e)}
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # --- Audio ---
    if audio and aud_model:
        suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await audio.read()
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            scores["audio"] = aud_model.predict(tmp_path)
            input_types.append("audio")
        except Exception as e:
            scores["audio"] = {"label": "error", "confidence": 0.0, "error": str(e)}
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # --- Fusion ---
    fused = fuse(scores)

    # --- Store to DB ---
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)

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

    return AnalysisResponse(
        id=analysis_id,
        timestamp=timestamp.isoformat(),
        threat_score=fused["threat_score"],
        verdict=fused["verdict"],
        consistency=fused.get("consistency", "unanimous"),
        breakdown=fused["breakdown"],
    )


@router.get("/analyses")
async def list_analyses(
    limit: int = 20,
    verdict: str | None = None,
    min_risk: float | None = None,
    max_risk: float | None = None,
    input_type: str | None = None,
):
    """List recent analyses with optional filters."""
    async with async_session() as session:
        from sqlalchemy import select, desc

        query = select(Analysis).order_by(desc(Analysis.timestamp)).limit(limit)
        if verdict:
            query = query.where(Analysis.verdict == verdict)
        if min_risk is not None:
            query = query.where(Analysis.threat_score >= min_risk)
        if max_risk is not None:
            query = query.where(Analysis.threat_score <= max_risk)

        result = await session.execute(query)
        rows = result.scalars().all()

        # Filter by input_type in Python (JSON array contains)
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


@router.get("/analyze/{analysis_id}/report")
async def download_report(analysis_id: str):
    """Download a PDF report for a completed analysis."""
    async with async_session() as session:
        from sqlalchemy import select

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
