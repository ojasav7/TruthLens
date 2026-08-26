"""SQLAlchemy ORM models for TruthLens."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.sqlite import JSON

from backend.db.database import Base


class Analysis(Base):
    """Stores every analysis request and its fused result."""

    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    input_types = Column(JSON, nullable=False)  # e.g. ["text", "image"]
    threat_score = Column(Float, nullable=False)  # 0-100
    verdict = Column(String(20), nullable=False)  # Low / Review Needed / High Risk
    breakdown = Column(JSON, nullable=False)  # per-module scores
    raw_inputs = Column(JSON, nullable=True)  # optional: store input metadata
