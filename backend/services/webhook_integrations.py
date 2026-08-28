"""Webhook Integrations — Slack, Discord, PagerDuty.

Delivers alerts and notifications to external services.
"""

import os
import json
import logging
import hashlib
import time

logger = logging.getLogger("truthlens.webhook_integrations")

# In-memory webhook registry
_webhooks: dict[str, dict] = {}


def register_webhook(name: str, url: str, platform: str, events: list[str] | None = None, secret: str | None = None) -> dict:
    """Register a webhook endpoint."""
    wh_id = f"WH-{hashlib.sha256(f'{name}{url}'.encode()).hexdigest()[:8].upper()}"
    webhook = {
        "id": wh_id,
        "name": name,
        "url": url,
        "platform": platform,  # slack, discord, pagerduty, custom
        "events": events or ["alert", "analysis_complete"],
        "secret": secret,
        "enabled": True,
        "created_at": time.time(),
        "last_triggered": None,
        "failure_count": 0,
    }
    _webhooks[wh_id] = webhook
    return webhook


def remove_webhook(wh_id: str) -> bool:
    if wh_id in _webhooks:
        del _webhooks[wh_id]
        return True
    return False


def list_webhooks() -> list[dict]:
    return list(_webhooks.values())


def dispatch_webhook(event_type: str, payload: dict) -> list[dict]:
    """Dispatch an event to all matching webhooks."""
    import requests
    results = []
    for wh_id, wh in _webhooks.items():
        if not wh["enabled"]:
            continue
        if event_type not in wh.get("events", []):
            continue

        formatted = _format_for_platform(wh["platform"], event_type, payload)
        try:
            resp = requests.post(wh["url"], json=formatted, timeout=10)
            wh["last_triggered"] = time.time()
            wh["failure_count"] = 0 if resp.ok else wh.get("failure_count", 0) + 1
            results.append({"webhook_id": wh_id, "status": "sent", "code": resp.status_code})
        except Exception as e:
            wh["failure_count"] = wh.get("failure_count", 0) + 1
            results.append({"webhook_id": wh_id, "status": "failed", "error": str(e)})
            logger.error("Webhook %s failed: %s", wh_id, e)

    return results


def _format_for_platform(platform: str, event_type: str, payload: dict) -> dict:
    """Format payload for the target platform."""
    if platform == "slack":
        return _format_slack(event_type, payload)
    elif platform == "discord":
        return _format_discord(event_type, payload)
    elif platform == "pagerduty":
        return _format_pagerduty(event_type, payload)
    return {"event": event_type, "data": payload}


def _format_slack(event_type: str, payload: dict) -> dict:
    threat = payload.get("threat_score", 0)
    verdict = payload.get("verdict", "unknown")
    color = "#ef4444" if threat >= 70 else "#f59e0b" if threat >= 30 else "#22c55e"
    return {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"🔍 TruthLens Alert: {event_type}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Verdict:*\n{verdict}"},
                {"type": "mrkdwn", "text": f"*Threat Score:*\n{threat}/100"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": payload.get("message", "")}},
        ],
        "attachments": [{"color": color, "fields": [{"title": "Details", "value": json.dumps(payload)[:500], "short": False}]}],
    }


def _format_discord(event_type: str, payload: dict) -> dict:
    threat = payload.get("threat_score", 0)
    verdict = payload.get("verdict", "unknown")
    color = 0xef4444 if threat >= 70 else 0xf59e0b if threat >= 30 else 0x22c55e
    return {
        "embeds": [{
            "title": f"🔍 TruthLens: {event_type}",
            "description": payload.get("message", ""),
            "color": color,
            "fields": [
                {"name": "Verdict", "value": verdict, "inline": True},
                {"name": "Threat Score", "value": f"{threat}/100", "inline": True},
            ],
            "timestamp": payload.get("timestamp", ""),
        }]
    }


def _format_pagerduty(event_type: str, payload: dict) -> dict:
    threat = payload.get("threat_score", 0)
    severity = "critical" if threat >= 85 else "warning" if threat >= 50 else "info"
    return {
        "routing_key": os.getenv("PD_ROUTING_KEY", ""),
        "event_action": "trigger",
        "payload": {
            "summary": f"TruthLens {event_type}: {payload.get('verdict', 'unknown')} (threat: {threat})",
            "severity": severity,
            "source": "truthlens",
            "component": "detection",
            "custom_details": payload,
        },
    }
