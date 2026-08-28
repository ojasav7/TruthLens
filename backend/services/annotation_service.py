"""Evidence Annotation.

Analysts/reviewers attach structured observations to evidence.
Annotations never modify the original evidence — stored separately.
"""

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.annotation")

# In-memory store: evidence_id → [annotations]
_annotations: dict[str, list[dict]] = {}

ANNOTATION_TYPES = [
    "note", "highlight", "rectangle", "region", "arrow",
    "label", "timestamp", "frame_marker",
]


@dataclass
class Annotation:
    evidence_id: str
    annotation_type: str
    content: str
    author: str = "analyst"
    tags: list[str] = None
    status: str = "active"  # active, needs_verification, resolved
    frame_range: list[int] | None = None
    timestamp_range: list[float] | None = None
    text_span: list[int] | None = None
    region: dict | None = None  # {x, y, width, height}

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        d = asdict(self)
        d["id"] = str(uuid.uuid4())[:12]
        d["created_at"] = datetime.now(timezone.utc).isoformat()
        return d


def add_annotation(
    evidence_id: str,
    annotation_type: str,
    content: str,
    author: str = "analyst",
    tags: list[str] | None = None,
    **kwargs,
) -> dict:
    """Add an annotation to evidence."""
    ann = Annotation(
        evidence_id=evidence_id,
        annotation_type=annotation_type,
        content=content,
        author=author,
        tags=tags or [],
        **kwargs,
    )
    d = ann.to_dict()
    _annotations.setdefault(evidence_id, []).append(d)
    logger.info("Annotation added to %s by %s", evidence_id, author)
    return d


def get_annotations(evidence_id: str) -> list[dict]:
    """Get all annotations for an evidence item."""
    return list(_annotations.get(evidence_id, []))


def update_annotation_status(evidence_id: str, annotation_id: str, status: str) -> dict | None:
    """Update annotation status."""
    for ann in _annotations.get(evidence_id, []):
        if ann["id"] == annotation_id:
            ann["status"] = status
            ann["updated_at"] = datetime.now(timezone.utc).isoformat()
            return ann
    return None


def get_all_annotations() -> dict[str, list[dict]]:
    """Get all annotations (admin)."""
    return dict(_annotations)
