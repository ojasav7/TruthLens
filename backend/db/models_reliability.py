"""New DB models for next-generation reliability, security, and operations features.

Additive — does NOT modify existing models.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, Boolean, Integer
from sqlalchemy.dialects.sqlite import JSON
from backend.db.database import Base


class AnalysisJob(Base):
    """Async analysis job tracking."""
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: f"JOB-{uuid.uuid4().hex[:8].upper()}")
    analysis_id = Column(String(36), nullable=True)
    status = Column(String(20), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    priority = Column(String(10), default="NORMAL")  # LOW, NORMAL, HIGH
    progress = Column(Float, default=0.0)
    progress_detail = Column(JSON, default=dict)  # {"nlp": "done", "image": "running", ...}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    input_types = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)


class ModelComparison(Base):
    """Champion vs Challenger model evaluation."""
    __tablename__ = "model_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: f"MC-{uuid.uuid4().hex[:8].upper()}")
    modality = Column(String(20), nullable=False)
    champion_version = Column(String(20), nullable=False)
    challenger_version = Column(String(20), nullable=False)
    metrics = Column(JSON, default=dict)  # {accuracy, f1, auc, latency, etc}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="EVALUATING")  # EVALUATING, PROMOTED, REJECTED
    notes = Column(Text, nullable=True)


class RobustnessRun(Base):
    """Red Team robustness test run."""
    __tablename__ = "robustness_runs"

    id = Column(String(36), primary_key=True, default=lambda: f"RT-{uuid.uuid4().hex[:8].upper()}")
    analysis_id = Column(String(36), nullable=True)
    modality = Column(String(20), nullable=False)
    original_score = Column(Float, nullable=False)
    transformations = Column(JSON, default=list)  # [{name, score, diff}]
    robustness_score = Column(Float, nullable=True)
    worst_degradation = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_version = Column(String(20), nullable=True)


class MediaSimilarity(Base):
    """Near-duplicate media detection results."""
    __tablename__ = "media_similarities"

    id = Column(String(36), primary_key=True, default=lambda: f"SIM-{uuid.uuid4().hex[:8].upper()}")
    source_analysis_id = Column(String(36), nullable=False)
    match_analysis_id = Column(String(36), nullable=False)
    similarity_score = Column(Float, nullable=False)  # 0-100
    fingerprint_type = Column(String(20), default="perceptual")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SecurityEvent(Base):
    """Security event log — separate from audit trail."""
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)  # INVALID_UPLOAD, RATE_LIMIT, etc
    severity = Column(String(10), default="INFO")  # INFO, WARN, CRITICAL
    details = Column(JSON, default=dict)
    source_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InvestigationSnapshot(Base):
    """Point-in-time snapshot of investigation state."""
    __tablename__ = "investigation_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: f"SNAP-{uuid.uuid4().hex[:8].upper()}")
    case_id = Column(String(36), nullable=False)
    version = Column(Integer, nullable=False)
    analysis_id = Column(String(36), nullable=True)
    risk_score = Column(Float, nullable=True)
    verdict = Column(String(20), nullable=True)
    uncertainty = Column(String(10), nullable=True)
    evidence_ids = Column(JSON, default=list)
    model_versions = Column(JSON, default=dict)
    feature_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RetentionPolicy(Base):
    """Configurable data retention policies."""
    __tablename__ = "retention_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False, unique=True)  # media, reports, audit, metadata
    retention_days = Column(Integer, nullable=False)
    action = Column(String(20), default="DELETE")  # DELETE, ANONYMIZE
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TraceSpan(Base):
    """Observability trace for analysis pipeline steps."""
    __tablename__ = "trace_spans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(30), nullable=False)  # TL-TRACE-XXXXXXXX
    parent_id = Column(String(36), nullable=True)
    module_name = Column(String(50), nullable=False)
    status = Column(String(10), default="OK")  # OK, ERROR, TIMEOUT
    duration_ms = Column(Float, nullable=True)
    model_version = Column(String(20), nullable=True)
    error_category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(JSON, default=dict)


class GoldenTest(Base):
    """Golden regression test dataset entry."""
    __tablename__ = "golden_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    modality = Column(String(20), nullable=False)
    expected_label = Column(String(20), nullable=False)
    expected_confidence_min = Column(Float, nullable=True)
    expected_confidence_max = Column(Float, nullable=True)
    tolerance = Column(Float, default=0.1)
    category = Column(String(20), default="real")  # real, fake, mixed, edge_case
    rationale = Column(Text, nullable=True)
    input_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
