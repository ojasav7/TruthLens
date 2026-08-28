"""Investigation Timeline.

Chronological timeline of all investigation events with filtering.
"""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.timeline")

# In-memory store: case_id → [events]
_timelines: dict[str, list[dict]] = {}

TIMELINE_EVENT_TYPES = [
    "upload", "fingerprint", "analysis", "evidence_discovery",
    "source_discovery", "provenance_check", "fact_check",
    "conflict_detection", "model_comparison", "human_review",
    "annotation", "verdict_change", "report_generation",
    "export", "snapshot", "archive",
]


@dataclass
class TimelineEvent:
    case_id: str
    event_type: str
    timestamp: str = ""
    actor: str = "system"
    module: str | None = None
    evidence_id: str | None = None
    description: str = ""
    details: dict | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.details is None:
            self.details = {}

    def to_dict(self):
        d = asdict(self)
        d["id"] = str(uuid.uuid4())[:12]
        return d


def add_event(
    case_id: str,
    event_type: str,
    description: str = "",
    actor: str = "system",
    module: str | None = None,
    evidence_id: str | None = None,
    details: dict | None = None,
) -> dict:
    """Add a timeline event."""
    event = TimelineEvent(
        case_id=case_id,
        event_type=event_type,
        actor=actor,
        module=module,
        evidence_id=evidence_id,
        description=description,
        details=details,
    )
    d = event.to_dict()
    _timelines.setdefault(case_id, []).append(d)
    return d


def get_timeline(
    case_id: str,
    event_type: str | None = None,
    actor: str | None = None,
    module: str | None = None,
    evidence_id: str | None = None,
) -> list[dict]:
    """Get timeline with optional filters."""
    events = _timelines.get(case_id, [])
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]
    if actor:
        events = [e for e in events if e["actor"] == actor]
    if module:
        events = [e for e in events if e["module"] == module]
    if evidence_id:
        events = [e for e in events if e["evidence_id"] == evidence_id]
    return sorted(events, key=lambda e: e["timestamp"])
