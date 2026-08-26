"""Organization/Team Workspaces — multi-tenant investigation management."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.db.database import async_session
from backend.db.models_advanced import Organization, OrgMember, InvestigationCase, AuditEvent
from backend.services.audit_service import AuditService
from sqlalchemy import select

router = APIRouter(prefix="/orgs", tags=["Organizations"])
audit_service = AuditService()


class OrgCreate(BaseModel):
    name: str
    description: str = ""
    owner_id: str


class MemberAdd(BaseModel):
    user_id: str
    role: str = "member"  # admin, member, viewer


@router.post("")
async def create_org(body: OrgCreate):
    """Create an organization."""
    async with async_session() as session:
        org = Organization(name=body.name, description=body.description, owner_id=body.owner_id)
        session.add(org)
        await session.flush()
        # Owner is automatically an admin member
        session.add(OrgMember(org_id=org.id, user_id=body.owner_id, role="admin"))
        session.add(AuditEvent(case_id=org.id, event_type="ORG_CREATED", details={"name": body.name}))
        await session.commit()
        return {"org_id": org.id, "name": org.name, "owner": body.owner_id}


@router.get("")
async def list_orgs(limit: int = Query(20, ge=1, le=100)):
    """List all organizations."""
    async with async_session() as session:
        result = await session.execute(select(Organization).order_by(Organization.created_at.desc()).limit(limit))
        return [{"org_id": o.id, "name": o.name, "owner": o.owner_id, "created_at": o.created_at.isoformat()} for o in result.scalars().all()]


@router.get("/{org_id}")
async def get_org(org_id: str):
    """Get organization details with members."""
    async with async_session() as session:
        result = await session.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        mem_result = await session.execute(select(OrgMember).where(OrgMember.org_id == org_id))
        members = mem_result.scalars().all()

        # Get cases linked to this org
        case_result = await session.execute(select(InvestigationCase).where(InvestigationCase.owner == org_id).limit(20))
        cases = case_result.scalars().all()

        return {
            "org_id": org.id, "name": org.name, "description": org.description,
            "owner": org.owner_id, "created_at": org.created_at.isoformat(),
            "members": [{"user_id": m.user_id, "role": m.role, "joined": m.joined_at.isoformat()} for m in members],
            "case_count": len(cases),
        }


@router.post("/{org_id}/members")
async def add_member(org_id: str, body: MemberAdd):
    """Add a member to an organization."""
    async with async_session() as session:
        # Check org exists
        result = await session.execute(select(Organization).where(Organization.id == org_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check not already member
        existing = await session.execute(select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == body.user_id))
        if existing.scalar_one_or_none():
            return {"status": "already_member"}

        member = OrgMember(org_id=org_id, user_id=body.user_id, role=body.role)
        session.add(member)
        await session.commit()
        return {"status": "added", "user_id": body.user_id, "role": body.role}


@router.get("/{org_id}/cases")
async def get_org_cases(org_id: str, limit: int = Query(20)):
    """Get cases belonging to an organization."""
    async with async_session() as session:
        result = await session.execute(
            select(InvestigationCase).where(InvestigationCase.owner == org_id).order_by(InvestigationCase.created_at.desc()).limit(limit)
        )
        cases = result.scalars().all()
        return [{"case_id": c.id, "title": c.title, "status": c.status, "priority": c.priority, "verdict": c.final_verdict, "risk_score": c.final_risk_score} for c in cases]
