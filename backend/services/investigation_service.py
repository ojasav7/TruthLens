"""Investigation Service — wraps analyses in structured investigations."""

from backend.db.database import async_session
from backend.db.models import Analysis
from backend.db.models_advanced import InvestigationCase, Evidence, AuditEvent, ModelVersion, MediaFingerprint, EvidenceRelation
from backend.services.evidence_engine import EvidenceEngine
from backend.services.prioritization_service import calculate_priority

MODEL_VERSIONS = {"nlp": "1.0.0", "image": "1.0.0", "video": "1.0.0", "audio": "1.0.0", "fusion": "1.0.0"}


class InvestigationService:
    def __init__(self):
        self.evidence_engine = EvidenceEngine()

    async def create_from_analysis(self, analysis_id: str) -> dict:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
            analysis = result.scalar_one_or_none()
            if not analysis:
                return {"error": "Analysis not found"}

            # Collect evidence first (needed for prioritization)
            evidence_records = self.evidence_engine.collect_from_analysis({"breakdown": analysis.breakdown})

            # Calculate consistency from breakdown
            breakdown = analysis.breakdown or {}
            labels = set()
            for mod in ["text", "image", "video", "audio"]:
                if mod in breakdown and isinstance(breakdown[mod], dict):
                    labels.add(breakdown[mod].get("label"))
            consistency = "unanimous" if len(labels) <= 1 else "mixed"
            priority = calculate_priority(analysis.threat_score, evidence=evidence_records, consistency=consistency)

            case = InvestigationCase(
                title=f"Investigation for {analysis_id[:8]}",
                analysis_ids=[analysis_id],
                final_verdict=analysis.verdict,
                final_risk_score=analysis.threat_score,
                priority=priority,
            )
            session.add(case)
            await session.flush()

            for modality, version in MODEL_VERSIONS.items():
                session.add(ModelVersion(analysis_id=analysis_id, modality=modality, version=version))

            for ev_data in evidence_records:
                session.add(Evidence(case_id=case.id, analysis_id=analysis_id, **ev_data))

            session.add(AuditEvent(case_id=case.id, event_type="CASE_CREATED", details={"analysis_id": analysis_id, "priority": priority}))
            await session.commit()

            return {"case_id": case.id, "status": case.status, "verdict": case.final_verdict, "risk_score": case.final_risk_score, "priority": priority, "consistency": consistency, "evidence_count": len(evidence_records)}

    async def get_investigation(self, case_id: str) -> dict:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(InvestigationCase).where(InvestigationCase.id == case_id))
            case = result.scalar_one_or_none()
            if not case:
                return {"error": "Case not found"}

            ev_result = await session.execute(select(Evidence).where(Evidence.case_id == case_id))
            evidence = ev_result.scalars().all()

            audit_result = await session.execute(select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp))
            audits = audit_result.scalars().all()

            return {
                "case_id": case.id, "title": case.title, "status": case.status,
                "verdict": case.final_verdict, "risk_score": case.final_risk_score,
                "evidence": [{"id": e.id, "type": e.type, "description": e.description, "score": e.score, "impact": e.impact, "category": e.category} for e in evidence],
                "audit_trail": [{"event_type": a.event_type, "timestamp": a.timestamp.isoformat()} for a in audits],
                "strength": self.evidence_engine.calculate_strength([{"score": e.score} for e in evidence]),
                "agreement": self.evidence_engine.calculate_agreement([{"category": e.category} for e in evidence]),
            }
