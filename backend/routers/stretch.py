"""Stretch feature endpoints — Phase 8 plug-in modules."""

import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

router = APIRouter()


# --- OCR ---
class OCRResponse(BaseModel):
    text: str
    word_count: int
    available: bool
    error: str | None = None


@router.post("/ocr", response_model=OCRResponse)
async def extract_text_from_image(file: UploadFile = File(...)):
    """Extract text from an uploaded image using OCR."""
    from backend.services.ocr_service import extract_text
    from PIL import Image

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        result = extract_text(img)
        return OCRResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")


# --- EXIF ---
class EXIFResponse(BaseModel):
    has_exif: bool
    suspicious: bool
    signals: list[str]
    metadata: dict


@router.post("/exif", response_model=EXIFResponse)
async def analyze_image_metadata(file: UploadFile = File(...)):
    """Analyze image EXIF metadata for manipulation indicators."""
    from backend.services.exif_service import analyze_metadata
    from PIL import Image

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        result = analyze_metadata(img)
        return EXIFResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EXIF analysis failed: {e}")


# --- Credibility ---
class CredibilityRequest(BaseModel):
    url: str


class CredibilityResponse(BaseModel):
    domain: str
    credibility: str
    risk_score: float
    signals: list[str]


@router.post("/credibility", response_model=CredibilityResponse)
async def check_source_credibility(request: CredibilityRequest):
    """Check a URL's domain against known credibility lists."""
    from backend.services.credibility_service import check_url
    if not request.url or len(request.url) > 2048:
        raise HTTPException(status_code=400, detail="Invalid URL length")
    result = check_url(request.url)
    return CredibilityResponse(**result)


# --- Screenshot Investigation ---
class ScreenshotResponse(BaseModel):
    status: str
    extracted_text: str
    claims: list[dict]
    claim_count: int


@router.post("/screenshot")
async def investigate_screenshot(file: UploadFile = File(...)):
    """Investigate a screenshot: OCR → extract claims → ready for NLP analysis."""
    from backend.services.screenshot_service import investigate_screenshot as _investigate

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()
        result = _investigate(contents, file.filename or "screenshot.png")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot investigation failed: {e}")


# --- Claim Extraction ---
class ClaimRequest(BaseModel):
    text: str


@router.post("/claims")
async def extract_claims_endpoint(request: ClaimRequest):
    """Extract individual claims from text for independent analysis."""
    from backend.services.claim_extractor import extract_claims
    from backend.validation import validate_text
    validate_text(request.text)
    claims = extract_claims(request.text)
    return {"claims": claims, "count": len(claims)}
