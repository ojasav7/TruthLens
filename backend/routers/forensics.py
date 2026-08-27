"""Forensics & Intelligence router — AI text detection, image forensics, C2PA, URL intel, watermark, sentiment, webhooks, custody."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/forensics", tags=["Forensics & Intelligence"])


# ── AI Text Detection ───────────────────────────────────────────
class AITextRequest(BaseModel):
    text: str

@router.post("/detect-ai-text")
async def detect_ai_generated_text(body: AITextRequest):
    """Detect if text was written by ChatGPT/Claude/Gemini using perplexity + burstiness."""
    from backend.services.ai_text_detector import detect_ai_text
    from backend.validation import validate_text
    validate_text(body.text)
    return detect_ai_text(body.text)


# ── Image Forensics ─────────────────────────────────────────────
@router.post("/image-forensics")
async def image_forensics(file: UploadFile = File(...)):
    """Full image forensics: ELA + copy-move detection."""
    from backend.services.image_forensics import full_forensics
    from backend.validation import validate_upload
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    data = await validate_upload(file)
    return full_forensics(data)


# ── C2PA Content Credentials ────────────────────────────────────
@router.post("/c2pa")
async def parse_content_credentials(file: UploadFile = File(...)):
    """Parse C2PA / Content Credentials from an image for provenance."""
    from backend.services.c2pa_service import parse_c2pa
    from backend.validation import validate_upload
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    data = await validate_upload(file)
    return parse_c2pa(data)


# ── Social Media URL Intelligence ───────────────────────────────
class URLRequest(BaseModel):
    url: str

@router.post("/url-intelligence")
async def url_intelligence(body: URLRequest):
    """Analyze a URL for social media platform, bot signals, and credibility."""
    from backend.services.url_intelligence import analyze_url
    return analyze_url(body.url)


class BatchURLRequest(BaseModel):
    urls: list[str]

@router.post("/url-intelligence/batch")
async def batch_url_intelligence(body: BatchURLRequest):
    """Analyze multiple URLs at once."""
    from backend.services.url_intelligence import batch_analyze_urls
    if len(body.urls) > 20:
        raise HTTPException(status_code=400, detail="Max 20 URLs per batch")
    return {"results": batch_analyze_urls(body.urls), "count": len(body.urls)}


# ── Watermark Detection ─────────────────────────────────────────
@router.post("/watermark")
async def detect_watermarks(file: UploadFile = File(...)):
    """Detect invisible watermarks from AI image generators."""
    from backend.services.watermark_detector import detect_watermark
    from backend.validation import validate_upload
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    data = await validate_upload(file)
    return detect_watermark(data)


# ── Sentiment / Manipulation Detection ──────────────────────────
class TextAnalysisRequest(BaseModel):
    text: str

@router.post("/detect-manipulation")
async def detect_manipulation(body: TextAnalysisRequest):
    """Detect emotional manipulation tactics in text."""
    from backend.services.sentiment_detector import detect_manipulation as _detect
    from backend.validation import validate_text
    validate_text(body.text)
    return _detect(body.text)


@router.post("/text-health")
async def text_health_report(body: TextAnalysisRequest):
    """Full text health report: manipulation + AI detection + claims."""
    from backend.services.sentiment_detector import text_health_report as _report
    from backend.validation import validate_text
    validate_text(body.text)
    return _report(body.text)


# ── Webhook Notifications ───────────────────────────────────────
class WebhookCreate(BaseModel):
    url: str
    name: str = ""
    events: list[str] = []

@router.post("/webhooks")
async def create_webhook(body: WebhookCreate):
    """Register a webhook to receive high-risk alerts."""
    from backend.services.webhook_service import register_webhook
    return register_webhook(body.url, body.name, body.events or ["high_risk_detected"])


@router.get("/webhooks")
async def list_webhooks():
    """List all registered webhooks."""
    from backend.services.webhook_service import list_webhooks as _list
    return _list()


@router.delete("/webhooks/{webhook_id}")
async def remove_webhook(webhook_id: str):
    """Remove a webhook."""
    from backend.services.webhook_service import remove_webhook as _remove
    return _remove(webhook_id)


# ── Evidence Chain of Custody ───────────────────────────────────
class CustodyCreate(BaseModel):
    evidence_id: str
    description: str = "Evidence created"
    actor: str = "system"

@router.post("/custody")
async def create_custody_chain(body: CustodyCreate):
    """Start a chain of custody for an evidence item."""
    from backend.services.custody_service import create_chain
    return create_chain(body.evidence_id, {"description": body.description, "actor": body.actor})


class CustodyEntry(BaseModel):
    evidence_id: str
    action: str  # ACCESSED, TRANSFERRED, TRANSFORMED, REVIEWED
    description: str
    actor: str = "system"

@router.post("/custody/entry")
async def add_custody_entry(body: CustodyEntry):
    """Add a custody entry to an evidence chain."""
    from backend.services.custody_service import add_entry
    return add_entry(body.evidence_id, body.action, body.description, body.actor)


@router.get("/custody/{evidence_id}")
async def get_custody_chain(evidence_id: str):
    """Get the full custody chain and verify integrity."""
    from backend.services.custody_service import get_chain
    return get_chain(evidence_id)


@router.get("/custody/{evidence_id}/verify")
async def verify_custody(evidence_id: str):
    """Verify the integrity of a custody chain."""
    from backend.services.custody_service import verify_chain
    return verify_chain(evidence_id)
