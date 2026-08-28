"""Evidence Chain of Custody.

Permanent, auditable history for every piece of investigation evidence.
Each transition is traceable. Historical events are never overwritten.
"""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.custody")

# In-memory chain store: evidence_id → [events]
_chains: dict[str, list[dict]] = {}


@dataclass
class CustodyEvent:
    evidence_id: str
    event_type: str  # evidence_created, fingerprint_generated, analyzed, etc.
    actor: str  # "system" or reviewer ID
    previous_state: str | None = None
    new_state: str | None = None
    trace_id: str | None = None
    model_version: str | None = None
    details: dict | None = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self):
        d = asdict(self)
        d["id"] = str(uuid.uuid4())[:12]
        d["timestamp"] = datetime.now(timezone.utc).isoformat()
        return d


EVENT_TYPES = [
    "evidence_created", "evidence_uploaded", "fingerprint_generated",
    "evidence_analyzed", "evidence_verified", "evidence_modified",
    "evidence_annotated", "evidence_reviewed", "evidence_linked",
    "evidence_exported", "evidence_archived",
]


def record_event(
    evidence_id: str,
    event_type: str,
    actor: str = "system",
    previous_state: str | None = None,
    new_state: str | None = None,
    trace_id: str | None = None,
    model_version: str | None = None,
    details: dict | None = None,
) -> dict:
    """Record an immutable chain-of-custody event."""
    if event_type not in EVENT_TYPES:
        logger.warning("Unknown event type: %s", event_type)
    event = CustodyEvent(
        evidence_id=evidence_id,
        event_type=event_type,
        actor=actor,
        previous_state=previous_state,
        new_state=new_state,
        trace_id=trace_id,
        model_version=model_version,
        details=details,
    )
    d = event.to_dict()
    _chains.setdefault(evidence_id, []).append(d)
    logger.info("Custody: %s → %s by %s", evidence_id, event_type, actor)
    return d


def get_chain(evidence_id: str) -> list[dict]:
    """Get the full chain of custody for an evidence item."""
    return list(_chains.get(evidence_id, []))


def get_all_chains() -> dict[str, list[dict]]:
    """Get all chains (for admin/debug)."""
    return dict(_chains)
