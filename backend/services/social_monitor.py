"""Social Media Monitoring + Alert System.

ponytail: in-memory stores. For production, back with DB + scheduler.
"""

import hashlib
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger("truthlens.social_monitor")

_monitors: dict[str, dict] = {}
_alerts: list[dict] = []
_results: dict[str, dict] = {}

PLATFORMS = {"twitter": ["twitter.com", "x.com"], "facebook": ["facebook.com", "fb.com"], "instagram": ["instagram.com"], "youtube": ["youtube.com", "youtu.be"], "tiktok": ["tiktok.com"], "reddit": ["reddit.com"], "telegram": ["t.me"], "whatsapp": ["whatsapp.com", "wa.me"]}


def add_url_to_monitor(config: dict) -> dict:
    url = config.get("url", "")
    uid = hashlib.sha256(url.encode()).hexdigest()[:16]
    entry = {"id": uid, "url": url, "check_interval": config.get("check_interval", 3600), "alert_threshold": config.get("alert_threshold", 0.7), "platforms": config.get("platforms") or detect_platform(url), "enabled": True, "created_at": datetime.now(timezone.utc).isoformat(), "last_checked": None, "last_threat_score": None}
    _monitors[uid] = entry
    return entry


def list_monitored_urls() -> list[dict]:
    return list(_monitors.values())


def record_scan_result(url_id: str, threat_score: float, verdict: str, details: dict | None = None) -> dict | None:
    if url_id not in _monitors:
        return None
    entry = _monitors[url_id]
    entry["last_checked"] = datetime.now(timezone.utc).isoformat()
    entry["last_threat_score"] = threat_score
    _results[url_id] = {"threat_score": threat_score, "verdict": verdict, "details": details or {}, "scanned_at": entry["last_checked"]}
    if threat_score >= entry.get("alert_threshold", 0.7):
        alert = {"id": f"ALT-{hashlib.sha256(f'{url_id}{time.time()}'.encode()).hexdigest()[:8].upper()}", "url_id": url_id, "url": entry["url"], "threat_score": threat_score, "verdict": verdict, "severity": "HIGH" if threat_score >= 0.85 else "MEDIUM", "created_at": datetime.now(timezone.utc).isoformat(), "acknowledged": False}
        _alerts.append(alert)
        logger.warning("ALERT: %s threat=%.2f", entry["url"], threat_score)
        return alert
    return None


def get_alerts(acknowledged: bool | None = None, limit: int = 50) -> list[dict]:
    alerts = [a for a in _alerts if acknowledged is None or a["acknowledged"] == acknowledged]
    return list(reversed(alerts[-limit:]))


def acknowledge_alert(alert_id: str) -> bool:
    for a in _alerts:
        if a["id"] == alert_id:
            a["acknowledged"] = True
            return True
    return False


def get_scan_results(url_id: str) -> dict | None:
    return _results.get(url_id)


def detect_platform(url: str) -> list[str]:
    url_lower = url.lower()
    return [p for p, patterns in PLATFORMS.items() if any(pat in url_lower for pat in patterns)] or ["unknown"]
