# TruthLens Advanced Implementation Guide

> **Non-Breaking Rule:** Every change in this guide is ADDITIVE. Existing APIs, models, and tests remain untouched.

---

## Architecture Overview

```
EXISTING PIPELINE (UNCHANGED)
┌─────────────────────────────────────────────────────┐
│  Input → Models → Fusion → Score → Verdict → Report │
└─────────────────────────────────────────────────────┘

NEW ADDITIVE LAYER
┌─────────────────────────────────────────────────────┐
│  Evidence Engine → Investigation → Explanation       │
│  → Case Management → Human Review → Audit Trail     │
└─────────────────────────────────────────────────────┘
```

---

## Stage A: Core Product Layer

### A1. New Database Models

**File:** `backend/db/models_advanced.py`

```python
"""Advanced database models — additive, does NOT modify existing models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.sqlite import JSON
from backend.db.database import Base


class InvestigationCase(Base):
    """Groups analyses into investigation cases."""
    __tablename__ = "investigation_cases"

    id = Column(String(36), primary_key=True, default=lambda: f"TL-{uuid.uuid4().hex[:8].upper()}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="OPEN")  # OPEN, UNDER_REVIEW, RESOLVED, INCONCLUSIVE, ARCHIVED
    priority = Column(String(10), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    owner = Column(String(100), nullable=True)
    analysis_ids = Column(JSON, default=list)  # List of analysis IDs
    final_verdict = Column(String(20), nullable=True)
    final_risk_score = Column(Float, nullable=True)


class Evidence(Base):
    """Individual evidence records for investigations."""
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: f"E-{uuid.uuid4().hex[:8].upper()}")
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=True)
    source_module = Column(String(50), nullable=False)  # nlp, image, video, audio, provenance, factcheck, source
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    type = Column(String(50), nullable=False)  # VISUAL_EVIDENCE, AUDIO_EVIDENCE, TEXT_EVIDENCE, etc.
    description = Column(Text, nullable=False)
    score = Column(Float, nullable=True)  # 0-1 confidence
    impact = Column(String(10), default="MEDIUM")  # LOW, MEDIUM, HIGH
    category = Column(String(15), default="NEUTRAL")  # SUPPORTING, CONTRADICTING, NEUTRAL, UNKNOWN
    status = Column(String(20), default="COMPLETED")  # AVAILABLE, DISABLED, PROCESSING, COMPLETED, FAILED, UNAVAILABLE
    metadata_json = Column(JSON, default=dict)


class AuditEvent(Base):
    """Audit trail for investigations."""
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # CASE_CREATED, EVIDENCE_ADDED, etc.
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    details = Column(JSON, default=dict)
    actor = Column(String(100), default="system")


class ModelVersion(Base):
    """Tracks which model version made each prediction."""
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    modality = Column(String(20), nullable=False)  # nlp, image, video, audio, fusion
    version = Column(String(20), nullable=False)  # e.g., "1.0.0"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HumanReview(Base):
    """Human review records — never overwrites model predictions."""
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    reviewer_id = Column(String(100), nullable=False)
    verdict = Column(String(20), nullable=False)  # AUTHENTIC, MANIPULATED, MISLEADING, INCONCLUSIVE, NEEDS_MORE_EVIDENCE
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # NEVER store model_prediction here — keep it separate in Analysis table


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
```

### A2. Migration Script

**File:** `backend/db/migrate_advanced.py`

```python
"""Run once to create new tables without touching existing ones."""

import asyncio
from backend.db.database import engine, Base
from backend.db.models_advanced import (
    InvestigationCase, Evidence, AuditEvent,
    ModelVersion, HumanReview, FeedbackRecord
)


async def migrate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Advanced tables created successfully.")


if __name__ == "__main__":
    asyncio.run(migrate())
```

### A3. Evidence Engine Service

**File:** `backend/services/evidence_engine.py`

```python
"""Evidence Engine — consumes existing model outputs, never modifies them."""

from datetime import datetime, timezone


class EvidenceEngine:
    """Converts model outputs into structured evidence records."""

    def collect_from_analysis(self, analysis: dict) -> list[dict]:
        """Create evidence records from an existing analysis result."""
        evidence = []
        breakdown = analysis.get("breakdown", {})

        for modality in ["text", "image", "video", "audio"]:
            result = breakdown.get(modality)
            if result and isinstance(result, dict) and "label" in result:
                evidence.append({
                    "source_module": modality,
                    "type": f"{modality.upper()}_EVIDENCE",
                    "description": f"{modality.upper()} model: {result['label']} ({result.get('confidence', 0):.1%})",
                    "score": result.get("confidence", 0),
                    "impact": "HIGH" if result.get("confidence", 0) > 0.8 else "MEDIUM",
                    "category": "SUPPORTING" if result.get("label") in ("fake", "cloned") else "NEUTRAL",
                    "status": "COMPLETED",
                })
        return evidence

    def calculate_strength(self, evidence_list: list[dict]) -> float:
        """How strong/reliable is the collected evidence?"""
        if not evidence_list:
            return 0.0
        scores = [e.get("score", 0) for e in evidence_list if e.get("score") is not None]
        return sum(scores) / len(scores) if scores else 0.0

    def calculate_agreement(self, evidence_list: list[dict]) -> float:
        """How consistently do independent sources agree?"""
        if len(evidence_list) < 2:
            return 1.0
        categories = [e.get("category", "NEUTRAL") for e in evidence_list]
        if not categories:
            return 1.0
        from collections import Counter
        counts = Counter(categories)
        return counts.most_common(1)[0][1] / len(categories)
```

### A4. Investigation Service

**File:** `backend/services/investigation_service.py`

```python
"""Investigation Service — wraps analyses in structured investigations."""

from datetime import datetime, timezone
from backend.db.database import async_session
from backend.db.models import Analysis
from backend.db.models_advanced import InvestigationCase, AuditEvent, ModelVersion
from backend.services.evidence_engine import EvidenceEngine

# Model versions — update when models are retrained
MODEL_VERSIONS = {
    "nlp": "1.0.0",
    "image": "1.0.0",
    "video": "1.0.0",
    "audio": "1.0.0",
    "fusion": "1.0.0",
}


class InvestigationService:

    def __init__(self):
        self.evidence_engine = EvidenceEngine()

    async def create_from_analysis(self, analysis_id: str) -> dict:
        """Wrap an existing analysis in an investigation case."""
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
            analysis = result.scalar_one_or_none()

            if not analysis:
                return {"error": "Analysis not found"}

            # Create case
            case = InvestigationCase(
                title=f"Investigation for {analysis_id[:8]}",
                analysis_ids=[analysis_id],
                final_verdict=analysis.verdict,
                final_risk_score=analysis.threat_score,
            )
            session.add(case)
            await session.flush()

            # Record model versions
            for modality, version in MODEL_VERSIONS.items():
                mv = ModelVersion(
                    analysis_id=analysis_id,
                    modality=modality,
                    version=version,
                )
                session.add(mv)

            # Collect evidence
            analysis_dict = {
                "breakdown": analysis.breakdown,
            }
            evidence_records = self.evidence_engine.collect_from_analysis(analysis_dict)

            # Store evidence
            from backend.db.models_advanced import Evidence
            for ev_data in evidence_records:
                ev = Evidence(
                    case_id=case.id,
                    analysis_id=analysis_id,
                    **ev_data,
                )
                session.add(ev)

            # Audit trail
            audit = AuditEvent(
                case_id=case.id,
                event_type="CASE_CREATED",
                details={"analysis_id": analysis_id},
            )
            session.add(audit)

            await session.commit()

            return {
                "case_id": case.id,
                "status": case.status,
                "verdict": case.final_verdict,
                "risk_score": case.final_risk_score,
                "evidence_count": len(evidence_records),
            }

    async def get_investigation(self, case_id: str) -> dict:
        """Get full investigation with evidence."""
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(InvestigationCase).where(InvestigationCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            if not case:
                return {"error": "Case not found"}

            # Get evidence
            ev_result = await session.execute(
                select(Evidence).where(Evidence.case_id == case_id)
            )
            evidence = ev_result.scalars().all()

            # Get audit trail
            audit_result = await session.execute(
                select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp)
            )
            audits = audit_result.scalars().all()

            return {
                "case_id": case.id,
                "title": case.title,
                "status": case.status,
                "priority": case.priority,
                "verdict": case.final_verdict,
                "risk_score": case.final_risk_score,
                "evidence": [
                    {
                        "id": e.id,
                        "type": e.type,
                        "description": e.description,
                        "score": e.score,
                        "impact": e.impact,
                        "category": e.category,
                        "status": e.status,
                    }
                    for e in evidence
                ],
                "audit_trail": [
                    {
                        "event_type": a.event_type,
                        "timestamp": a.timestamp.isoformat(),
                        "details": a.details,
                    }
                    for a in audits
                ],
                "strength": self.evidence_engine.calculate_strength([
                    {"score": e.score} for e in evidence
                ]),
                "agreement": self.evidence_engine.calculate_agreement([
                    {"category": e.category} for e in evidence
                ]),
            }
```

### A5. Investigation Router

**File:** `backend/routers/investigations.py`

```python
"""Investigation endpoints — additive, does NOT modify existing routers."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.investigation_service import InvestigationService

router = APIRouter()
service = InvestigationService()


class InvestigationResponse(BaseModel):
    case_id: str
    status: str
    verdict: str | None
    risk_score: float | None
    evidence_count: int


@router.post("/investigations/{analysis_id}", response_model=InvestigationResponse)
async def create_investigation(analysis_id: str):
    """Create an investigation from an existing analysis."""
    result = await service.create_from_analysis(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/investigations/{case_id}")
async def get_investigation(case_id: str):
    """Get full investigation with evidence and audit trail."""
    result = await service.get_investigation(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
```

### A6. Register New Router (Additive)

**File:** `backend/main.py` — add ONE line:

```python
# Add after existing router imports
from backend.routers import investigations

# Add after existing include_router calls
app.include_router(investigations.router, tags=["Investigations"])
```

---

## Stage B: Advanced Intelligence

### B1. Contradiction Engine

**File:** `backend/services/contradiction_engine.py`

```python
"""Multimodal Contradiction Engine — consumes model outputs only."""


class ContradictionEngine:
    """Detects when modalities disagree with each other."""

    def analyze(self, breakdown: dict) -> dict:
        """
        Analyze modality agreement.

        Returns:
            {
                "status": "consistent" | "inconsistent",
                "score": float (0-1, higher = more consistent),
                "signals": list of contradiction signals
            }
        """
        active_modalities = {}
        for mod in ["text", "image", "video", "audio"]:
            result = breakdown.get(mod)
            if result and isinstance(result, dict) and "label" in result:
                active_modalities[mod] = result

        if len(active_modalities) < 2:
            return {"status": "insufficient_data", "score": 1.0, "signals": []}

        # Check for label disagreements
        labels = [r["label"] for r in active_modalities.values()]
        fake_count = sum(1 for l in labels if l in ("fake", "cloned"))
        real_count = sum(1 for l in labels if l == "real")

        signals = []
        if fake_count > 0 and real_count > 0:
            signals.append({
                "type": "label_disagreement",
                "description": f"{fake_count} modalities say fake/cloned, {real_count} say real",
                "confidence": abs(fake_count - real_count) / len(labels),
            })

        # Check confidence spread
        confidences = [r.get("confidence", 0) for r in active_modalities.values()]
        if max(confidences) - min(confidences) > 0.3:
            signals.append({
                "type": "confidence_spread",
                "description": f"Confidence ranges from {min(confidences):.1%} to {max(confidences):.1%}",
                "confidence": max(confidences) - min(confidences),
            })

        agreement = 1.0 - (len(signals) * 0.2)
        status = "consistent" if not signals else "inconsistent"

        return {
            "status": status,
            "score": round(max(agreement, 0), 2),
            "signals": signals,
        }
```

### B2. Video Timeline Service

**File:** `backend/services/video_timeline.py`

```python
"""Video Temporal Investigation — consumes existing per-frame scores."""


class VideoTimeline:
    """Groups consecutive high-risk frames into suspicious segments."""

    def detect_segments(self, per_frame_scores: list[dict], threshold: float = 0.7) -> list[dict]:
        """Group consecutive high-risk frames into segments."""
        if not per_frame_scores:
            return []

        segments = []
        current_segment = None

        for frame in per_frame_scores:
            score = frame.get("score", 0)
            frame_idx = frame.get("frame", 0)

            if score >= threshold:
                if current_segment is None:
                    current_segment = {"start_frame": frame_idx, "end_frame": frame_idx, "scores": [score]}
                else:
                    current_segment["end_frame"] = frame_idx
                    current_segment["scores"].append(score)
            else:
                if current_segment is not None:
                    segments.append(self._finalize_segment(current_segment))
                    current_segment = None

        if current_segment is not None:
            segments.append(self._finalize_segment(current_segment))

        return segments

    def _finalize_segment(self, segment: dict) -> dict:
        scores = segment["scores"]
        return {
            "start_frame": segment["start_frame"],
            "end_frame": segment["end_frame"],
            "frame_count": segment["end_frame"] - segment["start_frame"] + 1,
            "avg_risk": round(sum(scores) / len(scores), 4),
            "max_risk": round(max(scores), 4),
        }

    def get_timeline(self, per_frame_scores: list[dict]) -> list[dict]:
        """Return frame-by-frame risk for visualization."""
        return [
            {
                "frame": f.get("frame", 0),
                "risk": f.get("score", 0),
                "level": "high" if f.get("score", 0) >= 0.7 else "medium" if f.get("score", 0) >= 0.4 else "low",
            }
            for f in per_frame_scores
        ]
```

### B3. Explanation Engine

**File:** `backend/services/explanation_engine.py`

```python
"""Evidence Explanation Engine — human-readable explanations."""


class ExplanationEngine:
    """Generates human-readable explanations from evidence."""

    def explain(self, investigation: dict) -> dict:
        """Generate explanation from investigation data."""
        evidence = investigation.get("evidence", [])
        risk_score = investigation.get("risk_score", 0)
        verdict = investigation.get("verdict", "Low")

        primary_reasons = []
        unknown_items = []

        for ev in evidence:
            if ev.get("impact") == "HIGH" and ev.get("category") == "SUPPORTING":
                primary_reasons.append({
                    "reason": ev.get("description", ""),
                    "impact": "high",
                })
            elif ev.get("status") == "UNAVAILABLE":
                unknown_items.append(ev.get("description", "Unknown evidence"))

        # Safety: never say "definitely fake"
        if risk_score >= 70:
            summary = "The available evidence indicates elevated manipulation risk."
            action = "Human review recommended."
        elif risk_score >= 30:
            summary = "Mixed signals detected. Further analysis may be beneficial."
            action = "Consider additional evidence sources."
        else:
            summary = "The available evidence suggests low manipulation risk."
            action = "No immediate action required."

        return {
            "summary": summary,
            "primary_reasons": primary_reasons[:5],
            "unknown": unknown_items[:5],
            "recommended_action": action,
            "risk_score": risk_score,
            "verdict": verdict,
        }
```

---

## Stage C: Investigation Experience

### C1. Case Management Service

**File:** `backend/services/case_service.py`

```python
"""Case Management — groups analyses into investigation cases."""

from datetime import datetime, timezone
from backend.db.database import async_session
from backend.db.models_advanced import InvestigationCase, AuditEvent


class CaseService:

    async def create(self, title: str, description: str = None) -> dict:
        async with async_session() as session:
            case = InvestigationCase(title=title, description=description)
            session.add(case)
            await session.flush()

            audit = AuditEvent(
                case_id=case.id,
                event_type="CASE_CREATED",
                details={"title": title},
            )
            session.add(audit)
            await session.commit()

            return {"case_id": case.id, "status": case.status}

    async def add_analysis(self, case_id: str, analysis_id: str) -> dict:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(InvestigationCase).where(InvestigationCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            if not case:
                return {"error": "Case not found"}

            case.analysis_ids = case.analysis_ids or []
            if analysis_id not in case.analysis_ids:
                case.analysis_ids.append(analysis_id)

            audit = AuditEvent(
                case_id=case_id,
                event_type="ANALYSIS_ADDED",
                details={"analysis_id": analysis_id},
            )
            session.add(audit)
            await session.commit()
            return {"status": "added"}

    async def list_cases(self, status: str = None, limit: int = 20) -> list:
        async with async_session() as session:
            from sqlalchemy import select
            query = select(InvestigationCase).order_by(InvestigationCase.created_at.desc()).limit(limit)
            if status:
                query = query.where(InvestigationCase.status == status)
            result = await session.execute(query)
            cases = result.scalars().all()
            return [
                {
                    "case_id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "priority": c.priority,
                    "verdict": c.final_verdict,
                    "risk_score": c.final_risk_score,
                    "created_at": c.created_at.isoformat(),
                }
                for c in cases
            ]
```

### C2. Human Review Service

**File:** `backend/services/review_service.py`

```python
"""Human Review Queue — never overwrites model predictions."""

from datetime import datetime, timezone
from backend.db.database import async_session
from backend.db.models_advanced import HumanReview, InvestigationCase, AuditEvent


class ReviewService:

    async def queue_case(self, case_id: str, reason: str) -> dict:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(InvestigationCase).where(InvestigationCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            if not case:
                return {"error": "Case not found"}

            case.status = "UNDER_REVIEW"

            audit = AuditEvent(
                case_id=case_id,
                event_type="REVIEW_REQUESTED",
                details={"reason": reason},
            )
            session.add(audit)
            await session.commit()
            return {"status": "queued"}

    async def submit_review(self, case_id: str, reviewer_id: str, verdict: str, notes: str = None) -> dict:
        async with async_session() as session:
            review = HumanReview(
                case_id=case_id,
                reviewer_id=reviewer_id,
                verdict=verdict,
                notes=notes,
            )
            session.add(review)

            from sqlalchemy import select
            result = await session.execute(
                select(InvestigationCase).where(InvestigationCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            if case:
                case.status = "RESOLVED"
                case.final_verdict = verdict

            audit = AuditEvent(
                case_id=case_id,
                event_type="REVIEW_COMPLETED",
                details={"reviewer": reviewer_id, "verdict": verdict},
            )
            session.add(audit)
            await session.commit()
            return {"status": "reviewed", "verdict": verdict}

    async def get_queue(self) -> list:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(InvestigationCase)
                .where(InvestigationCase.status == "UNDER_REVIEW")
                .order_by(InvestigationCase.created_at.desc())
            )
            cases = result.scalars().all()
            return [
                {
                    "case_id": c.id,
                    "title": c.title,
                    "risk_score": c.final_risk_score,
                    "priority": c.priority,
                }
                for c in cases
            ]
```

---

## Stage D: Real-World Features

### D1. Screenshot Investigation

**File:** `backend/services/screenshot_investigation.py`

```python
"""Screenshot Investigation — OCR → Text → Claims → Fact-Check."""

from backend.services.ocr_service import extract_text
from backend.services.claim_extractor import ClaimExtractor


class ScreenshotInvestigation:
    """Investigate screenshots by extracting text and analyzing claims."""

    def __init__(self):
        self.claim_extractor = ClaimExtractor()

    def investigate(self, image_input) -> dict:
        """
        Screenshot → OCR → Text → Claims → Investigation.

        Rules:
        - OCR output feeds EXISTING NLP pipeline (no duplicate model)
        - Returns investigation-ready data
        """
        # Step 1: OCR
        ocr_result = extract_text(image_input)
        if not ocr_result.get("available"):
            return {
                "status": "ocr_unavailable",
                "error": ocr_result.get("error", "OCR not available"),
            }

        text = ocr_result.get("text", "")
        if not text.strip():
            return {
                "status": "no_text_found",
                "text": "",
                "claims": [],
            }

        # Step 2: Extract claims
        claims = self.claim_extractor.extract(text)

        return {
            "status": "completed",
            "text": text,
            "word_count": ocr_result.get("word_count", 0),
            "claims": claims,
            "pipeline": "screenshot → ocr → claims → ready_for_nlp",
        }
```

### D2. Claim Extractor

**File:** `backend/services/claim_extractor.py`

```python
"""Claim Extraction — converts text into individual claims."""


class ClaimExtractor:
    """Extract individual claims from text."""

    def extract(self, text: str) -> list[dict]:
        """
        Convert text into individual claims.

        Rules:
        - Simple sentence splitting (no ML model needed initially)
        - Each claim gets an importance score
        """
        if not text or not text.strip():
            return []

        # Split by sentence-ending punctuation
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        claims = []
        for i, sentence in enumerate(sentences[:10]):  # Max 10 claims
            # Simple heuristic: longer sentences with specific entities are more important
            importance = min(1.0, len(sentence) / 100 + 0.3)

            claims.append({
                "id": f"C{i+1}",
                "text": sentence,
                "importance": round(importance, 2),
            })

        return claims
```

---

## Stage E: Research Features

### E1. Robustness Lab

**File:** `backend/services/robustness_lab.py`

```python
"""Robustness Laboratory — test model performance under controlled modifications."""

import io
import numpy as np
from PIL import Image


class RobustnessLab:
    """Test predictions under various transformations."""

    def test_image(self, image_input, detector) -> dict:
        """Test image predictions under resize, compression, noise."""
        from PIL import Image as PILImage

        if isinstance(image_input, (str,)):
            img = PILImage.open(image_input)
        elif isinstance(image_input, PILImage.Image):
            img = image_input
        else:
            return {"error": "Unsupported input"}

        results = {}

        # Original
        orig_result = detector.predict(img)
        results["original"] = orig_result

        # Compressed (JPEG Q30)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=30)
        buf.seek(0)
        compressed = PILImage.open(buf)
        results["compressed_q30"] = detector.predict(compressed)

        # Resized (112x112)
        resized = img.resize((112, 112))
        results["resized_112"] = detector.predict(resized)

        # Noisy
        arr = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 25, arr.shape).astype(np.float32)
        noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        noisy = PILImage.fromarray(noisy_arr)
        results["noisy"] = detector.predict(noisy)

        # Calculate robustness score
        labels = [r.get("label") for r in results.values()]
        agreement = labels.count(labels[0]) / len(labels) if labels else 0

        return {
            "results": results,
            "robustness_score": round(agreement * 100, 1),
            "transformations_tested": len(results) - 1,
        }
```

### E2. Performance Monitor

**File:** `backend/services/performance_monitor.py`

```python
"""Performance Monitoring — track per-module latency."""

import time
from contextlib import contextmanager


class PerformanceMonitor:
    """Track analysis timing."""

    def __init__(self):
        self.timings = {}

    @contextmanager
    def track(self, module: str):
        """Context manager to time a module execution."""
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.timings[module] = round(elapsed * 1000, 2)  # ms

    def get_stats(self) -> dict:
        """Return all recorded timings."""
        total = sum(self.timings.values())
        return {
            "module_timings_ms": self.timings.copy(),
            "total_ms": round(total, 2),
            "bottleneck": max(self.timings, key=self.timings.get) if self.timings else None,
        }

    def reset(self):
        self.timings.clear()
```

---

## Stage F: Feature Flags

### F1. Feature Configuration

**File:** `backend/config/features.py`

```python
"""Feature flags — optional modules can be enabled/disabled."""

import os


class FeatureFlags:
    """Central feature flag configuration."""

    PROVENANCE_ENABLED = os.getenv("ENABLE_PROVENANCE", "false").lower() == "true"
    FACTCHECK_ENABLED = os.getenv("ENABLE_FACTCHECK", "false").lower() == "true"
    OCR_ENABLED = os.getenv("ENABLE_OCR", "true").lower() == "true"
    SOURCE_ANALYSIS_ENABLED = os.getenv("ENABLE_SOURCE_ANALYSIS", "true").lower() == "true"
    REVIEW_QUEUE_ENABLED = os.getenv("ENABLE_REVIEW_QUEUE", "true").lower() == "true"
    INVESTIGATION_MODE = os.getenv("ENABLE_INVESTIGATION", "true").lower() == "true"

    @classmethod
    def status(cls) -> dict:
        """Return current feature flag status."""
        return {
            "provenance": cls.PROVENANCE_ENABLED,
            "factcheck": cls.FACTCHECK_ENABLED,
            "ocr": cls.OCR_ENABLED,
            "source_analysis": cls.SOURCE_ANALYSIS_ENABLED,
            "review_queue": cls.REVIEW_QUEUE_ENABLED,
            "investigation_mode": cls.INVESTIGATION_MODE,
        }
```

---

## Testing Strategy

### Regression Test Gate

After EVERY stage, run:

```bash
# Must pass before proceeding
python -m pytest tests/ -v

# Verify existing API contracts unchanged
curl -X POST http://localhost:8000/predict/text \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'

# Verify new endpoints work
curl -X POST http://localhost:8000/investigations/{analysis_id}
```

### New Test Files

```
tests/test_investigations.py    # Stage A
tests/test_contradiction.py     # Stage B
tests/test_case_management.py   # Stage C
tests/test_screenshot.py        # Stage D
tests/test_robustness.py        # Stage E
```

---

## Implementation Checklist

### Stage A ✅
- [ ] Create `backend/db/models_advanced.py`
- [ ] Create `backend/db/migrate_advanced.py`
- [ ] Create `backend/services/evidence_engine.py`
- [ ] Create `backend/services/investigation_service.py`
- [ ] Create `backend/routers/investigations.py`
- [ ] Register router in `main.py`
- [ ] Run migration
- [ ] Test: existing 36 tests still pass
- [ ] Test: new investigation endpoints work

### Stage B
- [ ] Create `backend/services/contradiction_engine.py`
- [ ] Create `backend/services/video_timeline.py`
- [ ] Create `backend/services/explanation_engine.py`
- [ ] Test: contradiction detection works
- [ ] Test: video timeline segments detected

### Stage C
- [ ] Create `backend/services/case_service.py`
- [ ] Create `backend/services/review_service.py`
- [ ] Create `backend/routers/cases.py`
- [ ] Test: case CRUD works
- [ ] Test: review queue works

### Stage D
- [ ] Create `backend/services/screenshot_investigation.py`
- [ ] Create `backend/services/claim_extractor.py`
- [ ] Test: screenshot → OCR → claims pipeline
- [ ] Test: claims are extracted correctly

### Stage E
- [ ] Create `backend/services/robustness_lab.py`
- [ ] Create `backend/services/performance_monitor.py`
- [ ] Test: robustness tests run without modifying originals
- [ ] Test: performance stats are tracked

### Stage F
- [ ] Create `backend/config/features.py`
- [ ] Add feature flags to all optional modules
- [ ] Test: modules fail gracefully when disabled

---

## Non-Negotiable Rules

1. **Existing 36 tests must pass after every stage**
2. **Existing API contracts never change**
3. **Each feature fails independently** — C2PA error doesn't crash `/analyze`
4. **One feature at a time** — PLAN → IMPLEMENT → TEST → VERIFY → COMMIT
5. **No model rewrites** unless explicitly required
6. **Feature flags** for all optional modules
7. **Human labels never overwrite model predictions**
8. **Audit trail logs every change**

---

*This guide ensures TruthLens grows through modular extensions, not through increasingly complex core code.*
