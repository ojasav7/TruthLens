"""Image deepfake prediction + Grad-CAM explainability -- Phase 2"""

import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from PIL import Image

from backend.services.model_loader import get_image_model

router = APIRouter()


class PredictionResponse(BaseModel):
    label: str
    confidence: float


class ExplainResponse(BaseModel):
    label: str
    confidence: float
    explained_output: str
    class_index: int
    class_name: str
    heatmap_b64: str


async def _read_image(file: UploadFile) -> Image.Image:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    try:
        contents = await file.read()
        return Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")


@router.post("/image", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    img_model = get_image_model()
    if img_model is None:
        raise HTTPException(status_code=503, detail="Image model not loaded")
    img = await _read_image(file)
    return PredictionResponse(**img_model.predict(img))


@router.post("/image/explain", response_model=ExplainResponse)
async def predict_image_explain(file: UploadFile = File(...)):
    img_model = get_image_model()
    if img_model is None:
        raise HTTPException(status_code=503, detail="Image model not loaded")
    img = await _read_image(file)
    try:
        return ExplainResponse(**img_model.explain(img))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e}")
