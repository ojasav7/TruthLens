"""
Timeline & Narrative Investigation View Service
Provides visual timeline of post publication, edits, reposts,
source propagation patterns, and sharing history.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class TimelineEvent:
    """Represents an event in the investigation timeline."""
    event_id: str
    timestamp: str
    event_type: str  # publication, edit, share, repost, analysis, review
    source: str
    platform: Optional[str] = None
    url: Optional[str] = None
    details: dict = field(default_factory=dict)
    severity: str = "info"  # info, warning, critical
    analyst_notes: Optional[str] = None


@dataclass
class NarrativeInvestigation:
    """Complete narrative investigation for content."""
    content_id: str
    timeline: list = field(default_factory=list)
    propagation_patterns: list = field(default_factory=list)
    source_network: list = field(default_factory=list)
    key_moments: list = field(default_factory=list)
    summary: str = ""
    risk_assessment: str = ""
    created_at: str = ""
    updated_at: str = ""


class TimelineService:
    """Creates and manages investigation timelines."""
    
    # Platform categories
    PLATFORMS = {
        "twitter": {"type": "social", "reach": "high"},
        "facebook": {"type": "social", "reach": "high"},
        "instagram": {"type": "social", "reach": "medium"},
        "tiktok": {"type": "social", "reach": "high"},
        "youtube": {"type": "video", "reach": "high"},
        "reddit": {"type": "forum", "reach": "medium"},
        "news": {"type": "news", "reach": "high"},
        "blog": {"type": "blog", "reach": "low"},
    }
    
    def create_investigation(self, content_id: str) -> NarrativeInvestigation:
        """Create a new narrative investigation."""
        investigation = NarrativeInvestigation(
            content_id=content_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return investigation
    
    def add_publication_event(self, investigation: NarrativeInvestigation,
                            source: str, platform: str, url: str = None) -> NarrativeInvestigation:
        """Add publication event to timeline."""
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="publication",
            source=source,
            platform=platform,
            url=url,
            details={
                "platform_type": self.PLATFORMS.get(platform, {}).get("type", "unknown"),
                "estimated_reach": self.PLATFORMS.get(platform, {}).get("reach", "unknown"),
            },
            severity="info",
        )
        
        investigation.timeline.append(self._event_to_dict(event))
        investigation.updated_at = datetime.now(timezone.utc).isoformat()
        
        return investigation
    
    def add_edit_event(self, investigation: NarrativeInvestigation,
                      source: str, edit_type: str, changes: dict) -> NarrativeInvestigation:
        """Add content edit event to timeline."""
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="edit",
            source=source,
            details={
                "edit_type": edit_type,
                "changes": changes,
                "previous_version": changes.get("previous"),
                "new_version": changes.get("new"),
            },
            severity="warning" if edit_type in ["headline_change", "image_swap"] else "info",
        )
        
        investigation.timeline.append(self._event_to_dict(event))
        investigation.updated_at = datetime.now(timezone.utc).isoformat()
        
        return investigation
    
    def add_share_event(self, investigation: NarrativeInvestigation,
                       source: str, platform: str, url: str = None,
                       shares_count: int = 1) -> NarrativeInvestigation:
        """Add share/repost event to timeline."""
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="share",
            source=source,
            platform=platform,
            url=url,
            details={
                "shares_count": shares_count,
                "platform_type": self.PLATFORMS.get(platform, {}).get("type", "unknown"),
            },
            severity="info",
        )
        
        investigation.timeline.append(self._event_to_dict(event))
        investigation.propagation_patterns.append({
            "platform": platform,
            "shares": shares_count,
            "timestamp": event.timestamp,
        })
        investigation.updated_at = datetime.now(timezone.utc).isoformat()
        
        return investigation
    
    def add_analysis_event(self, investigation: NarrativeInvestigation,
                          analysis_id: str, result: dict) -> NarrativeInvestigation:
        """Add analysis result event to timeline."""
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="analysis",
            source="TruthLens",
            details={
                "analysis_id": analysis_id,
                "verdict": result.get("verdict", "unknown"),
                "threat_score": result.get("threat_score", 0),
            },
            severity="critical" if result.get("threat_score", 0) > 70 else "warning",
        )
        
        investigation.timeline.append(self._event_to_dict(event))
        investigation.key_moments.append({
            "type": "analysis_complete",
            "timestamp": event.timestamp,
            "verdict": result.get("verdict"),
        })
        investigation.updated_at = datetime.now(timezone.utc).isoformat()
        
        return investigation
    
    def add_review_event(self, investigation: NarrativeInvestigation,
                        reviewer_id: str, action: str, details: dict) -> NarrativeInvestigation:
        """Add review event to timeline."""
        event = TimelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="review",
            source=reviewer_id,
            details=details,
            severity="info",
        )
        
        investigation.timeline.append(self._event_to_dict(event))
        investigation.updated_at = datetime.now(timezone.utc).isoformat()
        
        return investigation
    
    def generate_summary(self, investigation: NarrativeInvestigation) -> str:
        """Generate a summary of the investigation."""
        timeline = investigation.timeline
        if not timeline:
            return "No events recorded yet."
        
        events_by_type = {}
        for event in timeline:
            event_type = event.get("event_type", "unknown")
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        summary_parts = []
        summary_parts.append(f"Investigation contains {len(timeline)} events.")
        
        if "publication" in events_by_type:
            summary_parts.append(f"Content was published {events_by_type['publication']} time(s).")
        
        if "edit" in events_by_type:
            summary_parts.append(f"Content was edited {events_by_type['edit']} time(s).")
        
        if "share" in events_by_type:
            total_shares = sum(e.get("details", {}).get("shares_count", 1) 
                             for e in timeline if e.get("event_type") == "share")
            summary_parts.append(f"Content was shared {total_shares} time(s) across platforms.")
        
        if "analysis" in events_by_type:
            analyses = [e for e in timeline if e.get("event_type") == "analysis"]
            if analyses:
                latest = analyses[-1]
                verdict = latest.get("details", {}).get("verdict", "unknown")
                summary_parts.append(f"Latest analysis verdict: {verdict}.")
        
        return " ".join(summary_parts)
    
    def _event_to_dict(self, event: TimelineEvent) -> dict:
        """Convert event to dictionary."""
        return {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "source": event.source,
            "platform": event.platform,
            "url": event.url,
            "details": event.details,
            "severity": event.severity,
            "analyst_notes": event.analyst_notes,
        }


# Singleton instance
_timeline_service = None


def get_timeline_service() -> TimelineService:
    """Get or create singleton timeline service."""
    global _timeline_service
    if _timeline_service is None:
        _timeline_service = TimelineService()
    return _timeline_service
