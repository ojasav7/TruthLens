"""Screenshot Investigation — OCR → claims → existing NLP pipeline. No duplicate models."""

from backend.services.ocr_service import extract_text
from backend.services.claim_extractor import extract_claims
import io
from PIL import Image


def investigate_screenshot(image_bytes: bytes, filename: str = "screenshot.png") -> dict:
    """Full screenshot investigation pipeline: OCR → claims."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        ocr_result = extract_text(img)
    except Exception as e:
        return {"status": "error", "error": str(e), "claims": []}
    extracted_text = ocr_result.get("text", "")

    if not extracted_text.strip():
        return {
            "status": "no_text_extracted",
            "ocr": ocr_result,
            "claims": [],
            "message": "No readable text found in the image.",
        }

    # Step 2: Extract individual claims
    claims = extract_claims(extracted_text)

    # Step 3: The claims can then be fed into /predict/text for each claim
    # (This is done by the caller, not here — keeps this module focused)
    return {
        "status": "text_extracted",
        "ocr": ocr_result,
        "claims": claims,
        "extracted_text": extracted_text,
        "claim_count": len(claims),
    }
