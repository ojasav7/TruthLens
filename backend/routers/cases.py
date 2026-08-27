"""Case Management API — groups analyses into investigation cases."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.db.database import async_session
from backend.db.models_advanced import InvestigationCase, HumanReview, AuditEvent
from backend.services.audit_service import AuditService
from sqlalchemy import select

router = APIRouter(prefix="/cases", tags=["Case Management"])
audit_service = AuditService()


class CaseCreate(BaseModel):
    title: str
    description: str = ""
    analysis_ids: list[str] = []

    def model_post_init(self, __context):
        if not self.title.strip():
            raise ValueError("title must not be empty")


class ReviewSubmit(BaseModel):
    reviewer_id: str
    verdict: str  # AUTHENTIC | MANIPULATED | MISLEADING | INCONCLUSIVE | NEEDS_MORE_EVIDENCE
    notes: str = ""


@router.get("")
async def list_cases(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    verdict: str | None = Query(None),
    min_risk: float | None = Query(None),
    max_risk: float | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List investigation cases with optional filters."""
    async with async_session() as session:
        query = select(InvestigationCase).order_by(InvestigationCase.created_at.desc()).limit(limit)
        if status:
            query = query.where(InvestigationCase.status == status)
        if priority:
            query = query.where(InvestigationCase.priority == priority)
        if verdict:
            query = query.where(InvestigationCase.final_verdict == verdict)
        if min_risk is not None:
            query = query.where(InvestigationCase.final_risk_score >= min_risk)
        if max_risk is not None:
            query = query.where(InvestigationCase.final_risk_score <= max_risk)
        result = await session.execute(query)
        cases = result.scalars().all()
        return [
            {
                "case_id": c.id, "title": c.title, "status": c.status,
                "priority": c.priority, "verdict": c.final_verdict,
                "risk_score": c.final_risk_score, "created_at": c.created_at.isoformat(),
            }
            for c in cases
        ]


@router.post("")
async def create_case(body: CaseCreate):
    """Create a new investigation case."""
    async with async_session() as session:
        case = InvestigationCase(title=body.title, description=body.description, analysis_ids=body.analysis_ids)
        session.add(case)
        await session.flush()
        session.add(AuditEvent(case_id=case.id, event_type="CASE_CREATED", details={"title": body.title}))
        await session.commit()
        return {"case_id": case.id, "status": case.status}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Get a single case with its reviews."""
    async with async_session() as session:
        result = await session.execute(select(InvestigationCase).where(InvestigationCase.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        rev_result = await session.execute(select(HumanReview).where(HumanReview.case_id == case_id))
        reviews = rev_result.scalars().all()

        return {
            "case_id": case.id, "title": case.title, "description": case.description,
            "status": case.status, "priority": case.priority, "owner": case.owner,
            "analysis_ids": case.analysis_ids, "verdict": case.final_verdict,
            "risk_score": case.final_risk_score, "created_at": case.created_at.isoformat(),
            "reviews": [{"reviewer": r.reviewer_id, "verdict": r.verdict, "notes": r.notes, "timestamp": r.created_at.isoformat()} for r in reviews],
        }


@router.post("/{case_id}/review")
async def submit_review(case_id: str, body: ReviewSubmit):
    """Submit a human review for a case. Never overwrites model predictions."""
    valid_verdicts = {"AUTHENTIC", "MANIPULATED", "MISLEADING", "INCONCLUSIVE", "NEEDS_MORE_EVIDENCE"}
    if body.verdict.upper() not in valid_verdicts:
        raise HTTPException(status_code=400, detail=f"Invalid verdict. Must be one of: {valid_verdicts}")

    async with async_session() as session:
        result = await session.execute(select(InvestigationCase).where(InvestigationCase.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        review = HumanReview(case_id=case_id, reviewer_id=body.reviewer_id, verdict=body.verdict.upper(), notes=body.notes)
        session.add(review)

        # Update case status if resolved
        if body.verdict.upper() in ("AUTHENTIC", "MANIPULATED", "MISLEADING"):
            case.status = "RESOLVED"

        session.add(AuditEvent(case_id=case_id, event_type="REVIEW_COMPLETED", details={"verdict": body.verdict, "reviewer": body.reviewer_id}))
        await session.commit()
        return {"status": "review_submitted", "verdict": body.verdict.upper()}
