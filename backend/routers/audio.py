"""Audio voice clone prediction endpoint — Phase 4"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from backend.services.model_loader import get_audio_model

router = APIRouter()


class PredictionResponse(BaseModel):
    label: str
    confidence: float


class ExplanationResponse(BaseModel):
    label: str
    confidence: float
    explained_output: str
    top_coefficients: list
    base_value: float


ALLOWED = {"audio/", "video/"}


async def _run_audio(file: UploadFile, fn):
    """Validate, save temp file, run fn, cleanup."""
    model = get_audio_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Audio model not loaded")
    if not file.content_type or not any(file.content_type.startswith(p) for p in ALLOWED):
        raise HTTPException(status_code=400, detail="File must be audio or video")
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents); tmp.close()
    try:
        return fn(model, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)


@router.post("/audio", response_model=PredictionResponse)
async def predict_audio(file: UploadFile = File(...)):
    """Classify an uploaded audio file as real or cloned (voice clone)."""
    return PredictionResponse(**await _run_audio(file, lambda m, p: m.predict(p)))


@router.post("/audio/explain", response_model=ExplanationResponse)
async def explain_audio(file: UploadFile = File(...)):
    """Classify audio and explain which frequency bands drive the prediction."""
    return ExplanationResponse(**await _run_audio(file, lambda m, p: m.explain(p)))
