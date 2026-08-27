"""Initial schema — all TruthLens tables

Revision ID: 001_initial
Revises:
Create Date: 2026-08-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # analyses
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("input_types", sqlite.JSON, nullable=False),
        sa.Column("threat_score", sa.Float, nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("breakdown", sqlite.JSON, nullable=False),
        sa.Column("raw_inputs", sqlite.JSON, nullable=True),
    )

    # investigation_cases
    op.create_table(
        "investigation_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("priority", sa.String(10), nullable=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("analysis_ids", sqlite.JSON, nullable=True),
        sa.Column("final_verdict", sa.String(20), nullable=True),
        sa.Column("final_risk_score", sa.Float, nullable=True),
    )

    # evidence
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("investigation_cases.id"), nullable=False),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id"), nullable=True),
        sa.Column("source_module", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("impact", sa.String(10), nullable=True),
        sa.Column("category", sa.String(15), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("metadata_json", sqlite.JSON, nullable=True),
    )

    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("investigation_cases.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=True),
        sa.Column("details", sqlite.JSON, nullable=True),
        sa.Column("actor", sa.String(100), nullable=True),
    )

    # model_versions
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("modality", sa.String(20), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    # human_reviews
    op.create_table(
        "human_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("investigation_cases.id"), nullable=False),
        sa.Column("reviewer_id", sa.String(100), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    # feedback_records
    op.create_table(
        "feedback_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("model_prediction", sa.String(20), nullable=False),
        sa.Column("model_confidence", sa.Float, nullable=False),
        sa.Column("human_label", sa.String(20), nullable=False),
        sa.Column("review_reason", sa.Text, nullable=True),
        sa.Column("review_timestamp", sa.DateTime, nullable=True),
        sa.Column("model_version", sa.String(20), nullable=False),
    )

    # media_fingerprints
    op.create_table(
        "media_fingerprints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("media_id", sa.String(30), unique=True, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Float, nullable=True),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("filename", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id"), nullable=True),
        sa.Column("metadata_json", sqlite.JSON, nullable=True),
    )

    # evidence_relations
    op.create_table(
        "evidence_relations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("investigation_cases.id"), nullable=False),
        sa.Column("source_evidence_id", sa.String(36), nullable=False),
        sa.Column("target_evidence_id", sa.String(36), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("metadata_json", sqlite.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    # api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("org_id", sa.String(36), nullable=True),
        sa.Column("rate_limit", sa.String(20), nullable=True),
        sa.Column("is_active", sa.String(5), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
    )

    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("owner_id", sa.String(100), nullable=False),
        sa.Column("settings_json", sqlite.JSON, nullable=True),
    )

    # org_members
    op.create_table(
        "org_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=True),
        sa.Column("joined_at", sa.DateTime, nullable=True),
    )

    # stream_sessions
    op.create_table(
        "stream_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("results_json", sqlite.JSON, nullable=True),
    )


def downgrade() -> None:
    tables = [
        "stream_sessions", "org_members", "organizations", "api_keys",
        "evidence_relations", "media_fingerprints", "feedback_records",
        "human_reviews", "model_versions", "audit_events", "evidence",
        "investigation_cases", "analyses",
    ]
    for t in tables:
        op.drop_table(t)
