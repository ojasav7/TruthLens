"""Dashboard metrics and enhanced health check endpoints."""

import os
import time
import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import func, select, desc

from backend.db.database import async_session
from backend.db.models import Analysis
from backend.db.models_advanced import (
    InvestigationCase, Evidence, AuditEvent, HumanReview, MediaFingerprint
)

logger = logging.getLogger("truthlens")
router = APIRouter(tags=["Dashboard & Health"])

_start_time = time.time()


# ── Enriched Dashboard ──────────────────────────────────────────
@router.get("/dashboard")
async def dashboard_metrics():
    """Rich dashboard data: time series, top threats, modality distribution, recent activity."""
    async with async_session() as session:
        # Counts — separate queries avoid cartesian product
        total_analyses = (await session.execute(select(func.count(Analysis.id)))).scalar() or 0
        total_cases = (await session.execute(select(func.count(InvestigationCase.id)))).scalar() or 0
        total_evidence = (await session.execute(select(func.count(Evidence.id)))).scalar() or 0
        total_reviews = (await session.execute(select(func.count(HumanReview.id)))).scalar() or 0
        avg_score = round((await session.execute(select(func.avg(Analysis.threat_score)))).scalar() or 0, 2)

        # Verdict distribution
        verdict_rows = (await session.execute(
            select(Analysis.verdict, func.count(Analysis.id)).group_by(Analysis.verdict)
        )).all()
        verdict_dist = {row[0]: row[1] for row in verdict_rows}

        # Threat score histogram (buckets of 10) — computed from verdict distribution
        # to avoid loading all scores into memory
        histogram = {f"{i*10}-{i*10+10}": 0 for i in range(10)}
        if total_analyses > 0:
            score_rows = (await session.execute(select(Analysis.threat_score))).scalars().all()
            for s in score_rows:
                bucket = min(int(s // 10), 9)
                histogram[f"{bucket*10}-{bucket*10+10}"] += 1

        # Modality usage — computed from breakdown JSON without loading full objects
        all_inputs = (await session.execute(select(Analysis.input_types))).scalars().all()
        modality_counts = {"text": 0, "image": 0, "video": 0, "audio": 0}
        for inp in (all_inputs or []):
            for m in (inp or []):
                if m in modality_counts:
                    modality_counts[m] += 1

        # Recent activity (last 10 analyses + last 5 cases)
        recent_analyses = (await session.execute(
            select(Analysis).order_by(desc(Analysis.timestamp)).limit(10)
        )).scalars().all()
        recent_cases = (await session.execute(
            select(InvestigationCase).order_by(desc(InvestigationCase.created_at)).limit(5)
        )).scalars().all()

        # Case status distribution
        case_status_rows = (await session.execute(
            select(InvestigationCase.status, func.count(InvestigationCase.id))
            .group_by(InvestigationCase.status)
        )).all()
        case_statuses = {row[0]: row[1] for row in case_status_rows}

    return {
        "summary": {
            "total_analyses": total_analyses,
            "total_cases": total_cases,
            "total_evidence": total_evidence,
            "total_human_reviews": total_reviews,
            "avg_threat_score": avg_score,
        },
        "verdict_distribution": verdict_dist,
        "threat_histogram": histogram,
        "modality_usage": modality_counts,
        "case_statuses": case_statuses,
        "recent_analyses": [
            {
                "id": a.id,
                "verdict": a.verdict,
                "threat_score": a.threat_score,
                "input_types": a.input_types,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in recent_analyses
        ],
        "recent_cases": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
            }
            for c in recent_cases
        ],
    }


# ── Enhanced Health Check ───────────────────────────────────────
@router.get("/health/detailed")
async def detailed_health():
    """Health check that verifies DB, models, disk space, and uptime."""
    checks = {}
    uptime_s = round(time.time() - _start_time, 1)

    # DB check
    try:
        async with async_session() as session:
            await session.execute(select(func.count(Analysis.id)))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}

    # Models check
    try:
        from backend.services.model_loader import (
            get_nlp_model, get_image_model, get_video_model, get_audio_model
        )
        checks["models"] = {
            "nlp": "loaded" if get_nlp_model() else "not_loaded",
            "image": "loaded" if get_image_model() else "not_loaded",
            "video": "loaded" if get_video_model() else "not_loaded",
            "audio": "loaded" if get_audio_model() else "not_loaded",
        }
    except ImportError:
        checks["models"] = {"status": "skipped", "reason": "torch not installed"}

    # Disk space
    try:
        st = os.statvfs(".")
        free_gb = round((st.f_bavail * st.f_frsize) / (1024**3), 2)
        checks["disk"] = {"free_gb": free_gb, "status": "ok" if free_gb > 1 else "low"}
    except Exception:
        checks["disk"] = {"status": "unknown"}

    overall = "healthy" if all(
        c.get("status") in ("ok", "loaded", "not_loaded", "skipped", "unknown", "low")
        for c in checks.values()
    ) else "degraded"

    return {
        "status": overall,
        "uptime_seconds": uptime_s,
        "checks": checks,
    }
