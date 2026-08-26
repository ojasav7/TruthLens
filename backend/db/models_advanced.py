"""Advanced database models — additive, does NOT modify existing models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from backend.db.database import Base


class InvestigationCase(Base):
    """Groups analyses into investigation cases."""
    __tablename__ = "investigation_cases"

    id = Column(String(36), primary_key=True, default=lambda: f"TL-{uuid.uuid4().hex[:8].upper()}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="OPEN")
    priority = Column(String(10), default="MEDIUM")
    owner = Column(String(100), nullable=True)
    analysis_ids = Column(JSON, default=list)
    final_verdict = Column(String(20), nullable=True)
    final_risk_score = Column(Float, nullable=True)


class Evidence(Base):
    """Individual evidence records for investigations."""
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: f"E-{uuid.uuid4().hex[:8].upper()}")
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=True)
    source_module = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    impact = Column(String(10), default="MEDIUM")
    category = Column(String(15), default="NEUTRAL")
    status = Column(String(20), default="COMPLETED")
    metadata_json = Column(JSON, default=dict)


class AuditEvent(Base):
    """Audit trail for investigations."""
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(JSON, default=dict)
    actor = Column(String(100), default="system")


class ModelVersion(Base):
    """Tracks which model version made each prediction."""
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    modality = Column(String(20), nullable=False)
    version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HumanReview(Base):
    """Human review records — never overwrites model predictions."""
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    reviewer_id = Column(String(100), nullable=False)
    verdict = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FeedbackRecord(Base):
    """Human feedback for future active learning."""
    __tablename__ = "feedback_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    model_prediction = Column(String(20), nullable=False)
    model_confidence = Column(Float, nullable=False)
    human_label = Column(String(20), nullable=False)
    review_reason = Column(Text, nullable=True)
    review_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_version = Column(String(20), nullable=False)
