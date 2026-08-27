"""NLP text prediction + explainability endpoints — Phase 1"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.schemas import PredictionResponse
from backend.services.model_loader import get_nlp_model
from backend.validation import validate_text

router = APIRouter()


class TextRequest(BaseModel):
    text: str
    top_k: int = 10


class ExplainResponse(BaseModel):
    label: str
    confidence: float
    explained_output: str
    class_index: int
    class_name: str
    tokens: list[dict]
    base_value: float


@router.post("/text", response_model=PredictionResponse)
async def predict_text(request: TextRequest):
    """Classify text as fake or real news."""
    nlp = get_nlp_model()
    if nlp is None:
        raise HTTPException(status_code=503, detail="NLP model not loaded")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    text = validate_text(request.text)

    result = nlp.predict(text)
    return PredictionResponse(**result)


@router.post("/text/explain", response_model=ExplainResponse)
async def predict_text_explain(request: TextRequest):
    """Classify text with SHAP token-level explanations."""
    nlp = get_nlp_model()
    if nlp is None:
        raise HTTPException(status_code=503, detail="NLP model not loaded")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    text = validate_text(request.text)

    try:
        result = nlp.explain(text, top_k=request.top_k)
        return ExplainResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e}")
