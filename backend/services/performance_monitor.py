"""Performance Monitor — tracks analysis timing per modality. Dict-based, no external deps."""

import time
from contextlib import contextmanager


class PerformanceMonitor:
    def __init__(self):
        self.metrics: dict[str, list[float]] = {}

    @contextmanager
    def track(self, modality: str):
        """Context manager to time a code block."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.metrics.setdefault(modality, []).append(elapsed)

    def get_summary(self) -> dict:
        """Return averages and totals."""
        summary = {}
        for modality, times in self.metrics.items():
            summary[modality] = {
                "count": len(times),
                "avg_ms": round(sum(times) / len(times) * 1000, 1),
                "total_ms": round(sum(times) * 1000, 1),
                "max_ms": round(max(times) * 1000, 1),
            }
        total = sum(sum(t) for t in self.metrics.values())
        summary["total"] = {"avg_ms": round(total * 1000, 1), "modules_tracked": len(self.metrics)}
        return summary

    def reset(self):
        self.metrics.clear()


# Singleton
monitor = PerformanceMonitor()
