"""Async Analysis Job Service.

Long-running analyses run in background. Clients poll for progress.
Uses asyncio tasks — no external queue dependency.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.jobs")

# In-memory job store
_jobs: dict[str, dict] = {}


@dataclass
class JobInfo:
    job_id: str
    status: str  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    priority: str  # LOW, NORMAL, HIGH
    progress: float  # 0-100
    progress_detail: dict = None
    analysis_id: str | None = None
    error: str | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self):
        return asdict(self)


def create_job(priority: str = "NORMAL", input_types: list | None = None) -> dict:
    """Create a new analysis job."""
    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "priority": priority,
        "progress": 0.0,
        "progress_detail": {},
        "analysis_id": None,
        "error": None,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "input_types": input_types or [],
    }
    _jobs[job_id] = job
    logger.info("Job created: %s (priority=%s)", job_id, priority)
    return job


def update_job(job_id: str, **kwargs) -> dict | None:
    """Update job fields."""
    if job_id not in _jobs:
        return None
    _jobs[job_id].update(kwargs)
    return _jobs[job_id]


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


def list_jobs(status: str | None = None, limit: int = 50) -> list[dict]:
    jobs = list(_jobs.values())
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return jobs[-limit:]


def cancel_job(job_id: str) -> dict | None:
    if job_id not in _jobs:
        return None
    job = _jobs[job_id]
    if job["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
        return job
    job["status"] = "CANCELLED"
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    return job


async def run_async_analysis(job_id: str, analyze_fn, *args, **kwargs):
    """Run an analysis function in background, updating progress."""
    update_job(job_id, status="RUNNING", started_at=datetime.now(timezone.utc).isoformat())
    try:
        result = await analyze_fn(*args, **kwargs)
        update_job(
            job_id,
            status="COMPLETED",
            progress=100.0,
            analysis_id=result.get("id") if isinstance(result, dict) else None,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        return result
    except Exception as e:
        update_job(
            job_id,
            status="FAILED",
            error=str(e),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.error("Job %s failed: %s", job_id, e)
        raise
