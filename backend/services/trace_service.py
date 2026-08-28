"""Trace IDs + Observability.

Every analysis gets a unique trace ID. Tracks execution time, success/failure,
module name, model version per pipeline step.
"""

import time
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

logger = logging.getLogger("truthlens.trace")


@dataclass
class TraceSpanData:
    module: str
    status: str  # OK, ERROR, TIMEOUT
    duration_ms: float
    model_version: str = "unknown"
    error_category: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# In-memory trace store
_traces: dict[str, dict] = {}


def generate_trace_id() -> str:
    return f"TL-TRACE-{uuid.uuid4().hex[:8].upper()}"


def start_trace(input_types: list[str] | None = None) -> dict:
    """Start a new trace."""
    trace_id = generate_trace_id()
    _traces[trace_id] = {
        "trace_id": trace_id,
        "status": "RUNNING",
        "input_types": input_types or [],
        "spans": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "total_duration_ms": 0.0,
    }
    return _traces[trace_id]


class TraceTimer:
    """Context manager for timing a pipeline step."""
    def __init__(self, trace_id: str, module: str, model_version: str = "unknown"):
        self.trace_id = trace_id
        self.module = module
        self.model_version = model_version
        self._start = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self._start) * 1000
        status = "OK"
        error_cat = None
        if exc_type:
            status = "ERROR"
            error_cat = exc_type.__name__
        span = TraceSpanData(
            module=self.module,
            status=status,
            duration_ms=round(duration, 1),
            model_version=self.model_version,
            error_category=error_cat,
        )
        if self.trace_id in _traces:
            _traces[self.trace_id]["spans"].append(span.to_dict())
        logger.info("TRACE %s [%s] %.1fms %s", self.trace_id, self.module, duration, status)
        return False  # Don't suppress exceptions


def complete_trace(trace_id: str, status: str = "COMPLETED"):
    """Mark a trace as complete."""
    if trace_id not in _traces:
        return
    t = _traces[trace_id]
    t["status"] = status
    t["completed_at"] = datetime.now(timezone.utc).isoformat()
    t["total_duration_ms"] = round(
        sum(s.get("duration_ms", 0) for s in t["spans"]), 1
    )


def get_trace(trace_id: str) -> dict | None:
    return _traces.get(trace_id)


def list_traces(limit: int = 50) -> list[dict]:
    return list(reversed(list(_traces.values())[-limit:]))


def get_trace_summary() -> dict:
    """Summary stats for all traces."""
    total = len(_traces)
    completed = sum(1 for t in _traces.values() if t["status"] == "COMPLETED")
    failed = sum(1 for t in _traces.values() if t["status"] == "FAILED")
    avg_duration = 0.0
    if completed > 0:
        avg_duration = sum(t["total_duration_ms"] for t in _traces.values() if t["status"] == "COMPLETED") / completed
    return {
        "total_traces": total,
        "completed": completed,
        "failed": failed,
        "avg_duration_ms": round(avg_duration, 1),
    }
