"""Video deepfake prediction endpoint — Phase 3"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from backend.services.model_loader import get_video_model

router = APIRouter()


class FrameScore(BaseModel):
    frame: int
    score: float


class VideoPredictionResponse(BaseModel):
    label: str
    confidence: float
    per_frame_scores: list[FrameScore]


class FrameImportance(BaseModel):
    frame: int
    importance: float


class VideoExplainResponse(BaseModel):
    label: str
    confidence: float
    frame_importance: list[FrameImportance]


async def _run_video(file: UploadFile, fn):
    """Validate, save temp file, run fn, cleanup."""
    model = get_video_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Video model not loaded")
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents); tmp.close()
    try:
        return fn(model, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)


@router.post("/video", response_model=VideoPredictionResponse)
async def predict_video(file: UploadFile = File(...)):
    """Classify an uploaded video as real or fake (deepfake)."""
    result = await _run_video(file, lambda m, p: m.predict(p))
    return VideoPredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        per_frame_scores=result.get("per_frame_scores", []),
    )


@router.post("/video/explain", response_model=VideoExplainResponse)
async def explain_video(file: UploadFile = File(...), top_k: int = 5):
    """Explain which frames contribute most to the video classification."""
    result = await _run_video(file, lambda m, p: m.explain(p, top_k=top_k))
    return VideoExplainResponse(
        label=result["label"],
        confidence=result["confidence"],
        frame_importance=result.get("frame_importance", []),
    )
