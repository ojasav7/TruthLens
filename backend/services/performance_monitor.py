"""Performance Monitor — bare dict, no tracking yet. ponytail: add when profiling needed."""

# ponytail: monitor.track() was never called — stripped to dict only.
# Add timing wrappers around model.predict() calls when profiling matters.

_metrics: dict[str, list[float]] = {}


def record(modality: str, elapsed: float):
    _metrics.setdefault(modality, []).append(elapsed)


def get_summary() -> dict:
    if not _metrics:
        return {"message": "No timing data yet. Add monitor.record() calls to track."}
    summary = {}
    for mod, times in _metrics.items():
        summary[mod] = {"count": len(times), "avg_ms": round(sum(times) / len(times) * 1000, 1)}
    return summary
