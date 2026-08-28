"""Per-Key Rate Limiting + Usage Tracking.

Tracks requests per API key with sliding window rate limiting.
"""

import time
import logging
from collections import defaultdict

logger = logging.getLogger("truthlens.api_usage")

# Sliding window: key → [(timestamp, endpoint)]
# ponytail: in-memory sliding window. For production, use Redis sorted sets.
_usage: dict[str, list[tuple[float, str]]] = defaultdict(list)
_key_configs: dict[str, dict] = {}

WINDOW_SECONDS = 60


def register_api_key(key_hash: str, name: str, rate_limit: int = 100):
    """Register an API key with rate limit config."""
    _key_configs[key_hash] = {"name": name, "rate_limit": rate_limit}


def check_rate_limit(key_hash: str) -> dict:
    """Check if a key has exceeded its rate limit."""
    config = _key_configs.get(key_hash, {"rate_limit": 100})
    now = time.time()
    window_start = now - WINDOW_SECONDS
    # Clean old entries
    _usage[key_hash] = [(ts, ep) for ts, ep in _usage[key_hash] if ts > window_start]
    current_count = len(_usage[key_hash])
    limit = config["rate_limit"]
    return {
        "allowed": current_count < limit,
        "current": current_count,
        "limit": limit,
        "remaining": max(0, limit - current_count),
        "reset_at": window_start + WINDOW_SECONDS,
    }


def record_request(key_hash: str, endpoint: str):
    """Record a request for rate limiting."""
    _usage[key_hash].append((time.time(), endpoint))


def get_usage_stats(key_hash: str) -> dict:
    """Get usage stats for a key."""
    config = _key_configs.get(key_hash, {"name": "unknown", "rate_limit": 100})
    now = time.time()
    window_start = now - WINDOW_SECONDS
    recent = [(ts, ep) for ts, ep in _usage.get(key_hash, []) if ts > window_start]
    by_endpoint = {}
    for _, ep in recent:
        by_endpoint[ep] = by_endpoint.get(ep, 0) + 1
    return {
        "name": config["name"],
        "requests_last_minute": len(recent),
        "rate_limit": config["rate_limit"],
        "by_endpoint": by_endpoint,
    }
