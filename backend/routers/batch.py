"""Batch analysis, full-text search, and data export endpoints."""

import csv
import io
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, File, Form, UploadFile, Query, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.db.database import async_session
from backend.db.models import Analysis
from sqlalchemy import select, desc, or_
from backend.validation import validate_text, MAX_BATCH_ITEMS
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("truthlens")
router = APIRouter(tags=["Batch & Export"])
limiter = Limiter(key_func=get_remote_address)


# ── Batch Analysis ──────────────────────────────────────────────
class BatchItem(BaseModel):
    text: str | None = None

class BatchRequest(BaseModel):
    items: list[BatchItem]


@router.post("/analyze/batch")
@limiter.limit("10/minute")
async def analyze_batch(request: Request, body: BatchRequest):
    """Analyze multiple text inputs in one request. Returns array of results."""
    from models.fusion.fuse import fuse
    from backend.services.model_loader import get_nlp_model

    nlp = get_nlp_model()
    if nlp is None:
        raise HTTPException(status_code=503, detail="NLP model not loaded")

    results = []
    if len(body.items) > MAX_BATCH_ITEMS:
        raise HTTPException(status_code=400, detail=f"Too many items: {len(body.items)} (max {MAX_BATCH_ITEMS})")

    for idx, item in enumerate(body.items):
        if not item.text or not item.text.strip():
            results.append({"index": idx, "error": "empty text"})
            continue
        try:
            text = validate_text(item.text)
            pred = nlp.predict(text)
            fused = fuse({"text": pred})
            analysis_id = str(uuid.uuid4())
            ts = datetime.now(timezone.utc)

            async with async_session() as session:
                record = Analysis(
                    id=analysis_id,
                    timestamp=ts,
                    input_types=["text"],
                    threat_score=fused["threat_score"],
                    verdict=fused["verdict"],
                    breakdown=fused["breakdown"],
                )
                session.add(record)
                await session.commit()

            results.append({
                "index": idx,
                "id": analysis_id,
                "verdict": fused["verdict"],
                "threat_score": fused["threat_score"],
            })
        except Exception as e:
            results.append({"index": idx, "error": str(e)})

    return {"count": len(results), "results": results}


# ── Full-Text Search ────────────────────────────────────────────
@router.get("/search")
@limiter.limit("30/minute")
async def search(request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search across analyses and investigation cases by text content."""
    async with async_session() as session:
        # Search analyses — match verdict
        from backend.db.models_advanced import InvestigationCase

        from sqlalchemy import cast, String as SAString

        a_result = await session.execute(
            select(Analysis)
            .where(or_(
                Analysis.verdict.ilike(f"%{q}%"),
                cast(Analysis.input_types, SAString).ilike(f"%{q}%"),
            ))
            .order_by(desc(Analysis.timestamp))
            .limit(limit)
        )
        analyses = [
            {
                "type": "analysis",
                "id": r.id,
                "verdict": r.verdict,
                "threat_score": r.threat_score,
                "input_types": r.input_types,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in a_result.scalars().all()
        ]

        # Search cases — match title, description, status
        c_result = await session.execute(
            select(InvestigationCase)
            .where(or_(
                InvestigationCase.title.ilike(f"%{q}%"),
                InvestigationCase.description.ilike(f"%{q}%"),
                InvestigationCase.status.ilike(f"%{q}%"),
            ))
            .order_by(desc(InvestigationCase.created_at))
            .limit(limit)
        )
        cases = [
            {
                "type": "case",
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
            }
            for c in c_result.scalars().all()
        ]

    combined = sorted(analyses + cases, key=lambda x: x.get("timestamp") or x.get("created_at", ""), reverse=True)
    return {"query": q, "total": len(combined[:limit]), "results": combined[:limit]}


# ── CSV/JSON Export ─────────────────────────────────────────────
@router.get("/export/analyses")
@limiter.limit("10/minute")
async def export_analyses(request: Request,
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(100, ge=1, le=10000),
):
    """Export analyses as JSON or CSV."""
    async with async_session() as session:
        result = await session.execute(
            select(Analysis).order_by(desc(Analysis.timestamp)).limit(limit)
        )
        rows = result.scalars().all()

    data = [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "input_types": ",".join(r.input_types) if r.input_types else "",
            "threat_score": r.threat_score,
            "verdict": r.verdict,
            "breakdown": r.breakdown,
        }
        for r in rows
    ]

    if format == "csv":
        if not data:
            raise HTTPException(status_code=404, detail="No data to export")
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=data[0].keys(), extrasaction="ignore")
        writer.writeheader()
        for row in data:
            flat = {k: v for k, v in row.items() if k != "breakdown"}
            flat["text_label"] = (row.get("breakdown") or {}).get("text", {}).get("label", "")
            bd = row.get("breakdown") or {}
            flat["image_label"] = (bd.get("image") or {}).get("label", "")
            flat["video_label"] = (bd.get("video") or {}).get("label", "")
            flat["audio_label"] = (bd.get("audio") or {}).get("label", "")
            writer.writerow(flat)

        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=truthlens_analyses.csv"},
        )

    return {"count": len(data), "analyses": data}


@router.get("/export/cases")
@limiter.limit("10/minute")
async def export_cases(request: Request,
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(100, ge=1, le=10000),
):
    """Export investigation cases as JSON or CSV."""
    from backend.db.models_advanced import InvestigationCase

    async with async_session() as session:
        result = await session.execute(
            select(InvestigationCase).order_by(desc(InvestigationCase.created_at)).limit(limit)
        )
        rows = result.scalars().all()

    data = [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description or "",
            "status": c.status,
            "priority": c.priority,
            "owner": c.owner or "",
            "final_verdict": c.final_verdict or "",
            "final_risk_score": c.final_risk_score or 0,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]

    if format == "csv":
        if not data:
            raise HTTPException(status_code=404, detail="No data to export")
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=truthlens_cases.csv"},
        )

    return {"count": len(data), "cases": data}
