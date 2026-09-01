"""
Human-in-the-Loop Review Workflow Service
Adds reviewer comments, verdict reasons, confidence override,
final case disposition, and audit trail.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ReviewEvent:
    """Represents a review event in the audit trail."""
    event_id: str
    timestamp: str
    reviewer_id: str
    action: str
    details: dict
    previous_state: Optional[dict] = None
    new_state: Optional[dict] = None


@dataclass
class ReviewWorkflow:
    """Manages human review workflow for analyses."""
    analysis_id: str
    status: str  # pending, in_review, reviewed, escalated
    assigned_reviewer: Optional[str] = None
    reviewer_comments: list = field(default_factory=list)
    verdict_history: list = field(default_factory=list)
    confidence_overrides: list = field(default_factory=list)
    final_disposition: Optional[str] = None
    audit_trail: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class ReviewWorkflowManager:
    """Manages human review workflows."""
    
    def __init__(self):
        self.workflows = {}  # analysis_id -> ReviewWorkflow
    
    def create_workflow(self, analysis_id: str) -> ReviewWorkflow:
        """Create a new review workflow for an analysis."""
        workflow = ReviewWorkflow(
            analysis_id=analysis_id,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        
        # Add creation event to audit trail
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id="system",
            action="workflow_created",
            details={"status": "pending"},
        ))
        
        self.workflows[analysis_id] = workflow
        return workflow
    
    def assign_reviewer(self, analysis_id: str, reviewer_id: str) -> ReviewWorkflow:
        """Assign a reviewer to an analysis."""
        workflow = self._get_or_create(analysis_id)
        
        previous_state = {"assigned_reviewer": workflow.assigned_reviewer, "status": workflow.status}
        
        workflow.assigned_reviewer = reviewer_id
        workflow.status = "in_review"
        workflow.updated_at = datetime.now(timezone.utc).isoformat()
        
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id=reviewer_id,
            action="reviewer_assigned",
            details={"reviewer_id": reviewer_id},
            previous_state=previous_state,
            new_state={"assigned_reviewer": reviewer_id, "status": "in_review"},
        ))
        
        return workflow
    
    def add_comment(self, analysis_id: str, reviewer_id: str, comment: str, 
                    comment_type: str = "general") -> ReviewWorkflow:
        """Add a reviewer comment."""
        workflow = self._get_or_create(analysis_id)
        
        comment_entry = {
            "id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "comment": comment,
            "type": comment_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        workflow.reviewer_comments.append(comment_entry)
        workflow.updated_at = datetime.now(timezone.utc).isoformat()
        
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id=reviewer_id,
            action="comment_added",
            details={"comment_id": comment_entry["id"], "type": comment_type},
        ))
        
        return workflow
    
    def override_verdict(self, analysis_id: str, reviewer_id: str, 
                        new_verdict: str, reason: str) -> ReviewWorkflow:
        """Override the AI verdict with human judgment."""
        workflow = self._get_or_create(analysis_id)
        
        previous_verdict = workflow.verdict_history[-1] if workflow.verdict_history else None
        
        override_entry = {
            "id": str(uuid.uuid4()),
            "reviewer_id": reviewer_id,
            "previous_verdict": previous_verdict,
            "new_verdict": new_verdict,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        workflow.confidence_overrides.append(override_entry)
        workflow.verdict_history.append(new_verdict)
        workflow.updated_at = datetime.now(timezone.utc).isoformat()
        
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id=reviewer_id,
            action="verdict_overridden",
            details={
                "previous_verdict": previous_verdict,
                "new_verdict": new_verdict,
                "reason": reason,
            },
            previous_state={"verdict": previous_verdict},
            new_state={"verdict": new_verdict},
        ))
        
        return workflow
    
    def set_disposition(self, analysis_id: str, reviewer_id: str, 
                       disposition: str, notes: str = "") -> ReviewWorkflow:
        """Set final case disposition."""
        workflow = self._get_or_create(analysis_id)
        
        previous_disposition = workflow.final_disposition
        
        workflow.final_disposition = disposition
        workflow.status = "reviewed"
        workflow.updated_at = datetime.now(timezone.utc).isoformat()
        
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id=reviewer_id,
            action="disposition_set",
            details={
                "disposition": disposition,
                "notes": notes,
            },
            previous_state={"disposition": previous_disposition},
            new_state={"disposition": disposition},
        ))
        
        return workflow
    
    def escalate(self, analysis_id: str, reviewer_id: str, reason: str) -> ReviewWorkflow:
        """Escalate a case for senior review."""
        workflow = self._get_or_create(analysis_id)
        
        previous_state = {"status": workflow.status}
        
        workflow.status = "escalated"
        workflow.updated_at = datetime.now(timezone.utc).isoformat()
        
        workflow.audit_trail.append(self._create_event(
            analysis_id=analysis_id,
            reviewer_id=reviewer_id,
            action="case_escalated",
            details={"reason": reason},
            previous_state=previous_state,
            new_state={"status": "escalated"},
        ))
        
        return workflow
    
    def get_workflow(self, analysis_id: str) -> Optional[ReviewWorkflow]:
        """Get workflow for an analysis."""
        return self.workflows.get(analysis_id)
    
    def get_audit_trail(self, analysis_id: str) -> list:
        """Get audit trail for an analysis."""
        workflow = self.workflows.get(analysis_id)
        return workflow.audit_trail if workflow else []
    
    def _get_or_create(self, analysis_id: str) -> ReviewWorkflow:
        """Get or create workflow for an analysis."""
        if analysis_id not in self.workflows:
            return self.create_workflow(analysis_id)
        return self.workflows[analysis_id]
    
    def _create_event(self, analysis_id: str, reviewer_id: str, 
                     action: str, details: dict,
                     previous_state: Optional[dict] = None,
                     new_state: Optional[dict] = None) -> ReviewEvent:
        """Create a review event."""
        return ReviewEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            reviewer_id=reviewer_id,
            action=action,
            details=details,
            previous_state=previous_state,
            new_state=new_state,
        )
    
    def _workflow_to_dict(self, workflow: ReviewWorkflow) -> dict:
        """Convert workflow to dictionary."""
        return {
            "analysis_id": workflow.analysis_id,
            "status": workflow.status,
            "assigned_reviewer": workflow.assigned_reviewer,
            "reviewer_comments": workflow.reviewer_comments,
            "verdict_history": workflow.verdict_history,
            "confidence_overrides": workflow.confidence_overrides,
            "final_disposition": workflow.final_disposition,
            "audit_trail": [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp,
                    "reviewer_id": e.reviewer_id,
                    "action": e.action,
                    "details": e.details,
                    "previous_state": e.previous_state,
                    "new_state": e.new_state,
                }
                for e in workflow.audit_trail
            ],
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }


# Singleton instance
_review_manager = None


def get_review_manager() -> ReviewWorkflowManager:
    """Get or create singleton review workflow manager."""
    global _review_manager
    if _review_manager is None:
        _review_manager = ReviewWorkflowManager()
    return _review_manager
