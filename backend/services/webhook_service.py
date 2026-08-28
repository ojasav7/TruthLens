"""Webhook Notifications — push alerts for high-risk detections.

Stores webhook URLs and sends POST notifications when high-risk
content is detected. Supports custom and Slack-compatible webhooks.
"""

import hashlib
import secrets
import json
from datetime import datetime, timezone


# In-memory store (persistent store would use DB)
_webhooks: dict[str, dict] = {}


def register_webhook(url: str, name: str = "", events: list[str] | None = None) -> dict:
    """Register a webhook URL to receive notifications."""
    webhook_id = f"wh_{secrets.token_hex(8)}"
    _webhooks[webhook_id] = {
        "id": webhook_id,
        "url": url,
        "name": name or url[:50],
        "events": events or ["high_risk_detected", "case_created"],
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_triggered": None,
        "trigger_count": 0,
    }
    return {"id": webhook_id, "webhook_id": webhook_id, "status": "registered"}


def list_webhooks() -> list[dict]:
    """List all registered webhooks."""
    return list(_webhooks.values())


def remove_webhook(webhook_id: str) -> dict:
    """Remove a webhook."""
    if webhook_id in _webhooks:
        del _webhooks[webhook_id]
        return {"status": "removed"}
    return {"error": "Webhook not found"}


def send_notification(event: str, payload: dict) -> dict:
    """
    Send notification to all webhooks subscribed to this event.

    Returns dict of webhook_id → delivery status.
    """
    results = {}
    for wh_id, wh in _webhooks.items():
        if not wh["active"] or event not in wh["events"]:
            continue

        # Build notification payload
        notification = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_id": wh_id,
            "data": payload,
        }

        # Attempt delivery (non-blocking, fire-and-forget)
        try:
            import urllib.request
            req = urllib.request.Request(
                wh["url"],
                data=json.dumps(notification).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TruthLens-Webhook/1.0"},
                method="POST",
            )
            # Short timeout to avoid blocking
            response = urllib.request.urlopen(req, timeout=5)
            status = response.getcode()
            results[wh_id] = {"delivered": True, "status_code": status}

            wh["last_triggered"] = datetime.now(timezone.utc).isoformat()
            wh["trigger_count"] += 1

        except Exception as e:
            results[wh_id] = {"delivered": False, "error": str(e)}

    return results


def _format_slack(event_type: str, payload: dict) -> dict:
    """Format payload for Slack incoming webhook."""
    fields = [{"type": "mrkdwn", "text": f"*{event_type.replace('_', ' ').title()}*"}]
    for k, v in payload.items():
        fields.append({"type": "mrkdwn", "text": f"*{k}:* {v}"})
    return {"blocks": [{"type": "section", "text": fields[0]}, {"type": "section", "fields": fields[1:]}] if len(fields) > 1 else [{"type": "section", "text": fields[0]}]}


def _format_discord(event_type: str, payload: dict) -> dict:
    """Format payload for Discord webhook."""
    fields = []
    for k, v in payload.items():
        fields.append({"name": k, "value": str(v), "inline": True})
    return {"embeds": [{"title": event_type.replace('_', ' ').title(), "fields": fields}]}


def dispatch_webhook(event_type: str, payload: dict) -> dict:
    """Format and dispatch webhook to all registered URLs for an event type."""
    slack_payload = _format_slack(event_type, payload)
    return send_notification(event_type, slack_payload)


def notify_high_risk(analysis: dict) -> dict:
    """Send high-risk alert to all subscribed webhooks."""
    return send_notification("high_risk_detected", {
        "analysis_id": analysis.get("id", "unknown"),
        "threat_score": analysis.get("threat_score", 0),
        "verdict": analysis.get("verdict", "Unknown"),
        "input_types": analysis.get("input_types", []),
    })


def notify_case_created(case: dict) -> dict:
    """Send case creation alert."""
    return send_notification("case_created", {
        "case_id": case.get("case_id", "unknown"),
        "title": case.get("title", ""),
        "priority": case.get("priority", "MEDIUM"),
    })
