"""Smart Analysis Cache.

Avoids unnecessary repeated processing by checking fingerprints and
validating model version compatibility before reusing results.
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.cache")

# In-memory cache: sha256 → {result, model_versions, timestamp}
_cache: dict[str, dict] = {}
_MAX_CACHE = 1000


@dataclass
class CacheResult:
    hit: bool
    analysis_id: str | None = None
    message: str = ""
    reused_at: str | None = None

    def to_dict(self):
        return asdict(self)


def check_cache(sha256: str, model_versions: dict | None = None) -> dict:
    """Check if a compatible cached analysis exists."""
    if sha256 not in _cache:
        return CacheResult(hit=False, message="No cached analysis found").to_dict()

    entry = _cache[sha256]

    # Validate model version compatibility
    if model_versions and entry.get("model_versions"):
        for mod, ver in model_versions.items():
            if entry["model_versions"].get(mod) != ver:
                return CacheResult(
                    hit=False,
                    message=f"Model version mismatch for {mod}: cached={entry['model_versions'].get(mod)}, current={ver}",
                ).to_dict()

    return CacheResult(
        hit=True,
        analysis_id=entry.get("analysis_id"),
        message="Previous compatible analysis reused.",
        reused_at=entry.get("timestamp"),
    ).to_dict()


def store_cache(sha256: str, analysis_id: str, model_versions: dict | None = None):
    """Store an analysis result in cache."""
    _cache[sha256] = {
        "analysis_id": analysis_id,
        "model_versions": model_versions or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Evict oldest if full
    if len(_cache) > _MAX_CACHE:
        oldest_key = min(_cache, key=lambda k: _cache[k]["timestamp"])
        del _cache[oldest_key]


def get_cache_stats() -> dict:
    """Return cache statistics."""
    return {
        "size": len(_cache),
        "max_size": _MAX_CACHE,
        "entries": list(_cache.keys())[:20],
    }


def clear_cache():
    """Clear the entire cache."""
    _cache.clear()
