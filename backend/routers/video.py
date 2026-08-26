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


def _save_upload(file: UploadFile) -> str:
    """Save uploaded file to temp path, return path."""
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        return tmp.name


@router.post("/video", response_model=VideoPredictionResponse)
async def predict_video(file: UploadFile = File(...)):
    """Classify an uploaded video as real or fake (deepfake)."""
    vid_model = get_video_model()
    if vid_model is None:
        raise HTTPException(status_code=503, detail="Video model not loaded")

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    tmp_path = _save_upload(file)
    try:
        result = vid_model.predict(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return VideoPredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        per_frame_scores=result.get("per_frame_scores", []),
    )


@router.post("/video/explain", response_model=VideoExplainResponse)
async def explain_video(file: UploadFile = File(...), top_k: int = 5):
    """Explain which frames contribute most to the video classification."""
    vid_model = get_video_model()
    if vid_model is None:
        raise HTTPException(status_code=503, detail="Video model not loaded")

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    tmp_path = _save_upload(file)
    try:
        result = vid_model.explain(tmp_path, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video explain failed: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return VideoExplainResponse(
        label=result["label"],
        confidence=result["confidence"],
        frame_importance=result.get("frame_importance", []),
    )
