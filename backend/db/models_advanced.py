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


class MediaFingerprint(Base):
    """Unique identity for uploaded content."""
    __tablename__ = "media_fingerprints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_id = Column(String(30), unique=True, nullable=False)  # TL-M-XXXX-XXXX
    sha256 = Column(String(64), nullable=False)
    file_size = Column(Float, nullable=True)
    file_type = Column(String(50), nullable=True)
    filename = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=True)
    metadata_json = Column(JSON, default=dict)


class EvidenceRelation(Base):
    """Graph edges connecting evidence nodes."""
    __tablename__ = "evidence_relations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    source_evidence_id = Column(String(36), nullable=False)
    target_evidence_id = Column(String(36), nullable=False)
    relation_type = Column(String(50), nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    """API keys for public API access."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    org_id = Column(String(36), nullable=True)
    rate_limit = Column(String(20), default="100")  # requests per minute
    is_active = Column(String(5), default="true")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)


class Organization(Base):
    """Multi-tenant organizations."""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: f"ORG-{uuid.uuid4().hex[:8].upper()}")
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    owner_id = Column(String(100), nullable=False)
    settings_json = Column(JSON, default=dict)


class OrgMember(Base):
    """Organization members."""
    __tablename__ = "org_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String(100), nullable=False)
    role = Column(String(20), default="member")  # admin, member, viewer
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class StreamSession(Base):
    """Live streaming sessions."""
    __tablename__ = "stream_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True)
    status = Column(String(20), default="active")  # active, ended
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    results_json = Column(JSON, default=list)
