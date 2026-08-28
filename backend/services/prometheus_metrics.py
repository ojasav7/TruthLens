"""Prometheus Metrics Export.

Exposes metrics in Prometheus text format for Grafana dashboards.
"""

import time
import logging
from collections import defaultdict

logger = logging.getLogger("truthlens.metrics")

# Counters
_requests_total = defaultdict(int)
_errors_total = defaultdict(int)
_analyses_total = defaultdict(int)

# Histograms
_request_duration = defaultdict(list)

# Gauges
_active_jobs = 0
_model_loaded = {}

START_TIME = time.time()


def record_request(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Record a request metric."""
    key = f'{method}_{endpoint}_{status_code}'
    _requests_total[key] += 1
    _request_duration[endpoint].append(duration_ms)
    if status_code >= 500:
        _errors_total[endpoint] += 1


def record_analysis(modality: str, verdict: str):
    """Record an analysis metric."""
    _analyses_total[f'{modality}_{verdict}'] += 1


def set_model_status(modality: str, loaded: bool):
    """Set model load status."""
    _model_loaded[modality] = loaded


def set_active_jobs(count: int):
    global _active_jobs
    _active_jobs = count


def render_prometheus_metrics() -> str:
    """Render all metrics in Prometheus text format."""
    lines = []

    # Uptime
    lines.append("# HELP truthlens_uptime_seconds Application uptime in seconds")
    lines.append("# TYPE truthlens_uptime_seconds gauge")
    lines.append(f'truthlens_uptime_seconds {time.time() - START_TIME:.1f}')

    # Request counter
    lines.append("# HELP truthlens_requests_total Total HTTP requests")
    lines.append("# TYPE truthlens_requests_total counter")
    for key, val in sorted(_requests_total.items()):
        parts = key.rsplit("_", 2)
        if len(parts) == 3:
            method, endpoint, status = parts
            lines.append(f'truthlens_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {val}')

    # Error counter
    lines.append("# HELP truthlens_errors_total Total errors by endpoint")
    lines.append("# TYPE truthlens_errors_total counter")
    for endpoint, val in sorted(_errors_total.items()):
        lines.append(f'truthlens_errors_total{{endpoint="{endpoint}"}} {val}')

    # Analysis counter
    lines.append("# HELP truthlens_analyses_total Total analyses by modality and verdict")
    lines.append("# TYPE truthlens_analyses_total counter")
    for key, val in sorted(_analyses_total.items()):
        parts = key.split("_", 1)
        if len(parts) == 2:
            modality, verdict = parts
            lines.append(f'truthlens_analyses_total{{modality="{modality}",verdict="{verdict}"}} {val}')

    # Request duration
    lines.append("# HELP truthlens_request_duration_ms Request duration in milliseconds")
    lines.append("# TYPE truthlens_request_duration_ms summary")
    for endpoint, durations in sorted(_request_duration.items()):
        if durations:
            avg = sum(durations) / len(durations)
            p95 = sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else avg
            lines.append(f'truthlens_request_duration_ms{{endpoint="{endpoint}",quantile="0.5"}} {avg:.1f}')
            lines.append(f'truthlens_request_duration_ms{{endpoint="{endpoint}",quantile="0.95"}} {p95:.1f}')

    # Active jobs
    lines.append("# HELP truthlens_active_jobs Currently active analysis jobs")
    lines.append("# TYPE truthlens_active_jobs gauge")
    lines.append(f'truthlens_active_jobs {_active_jobs}')

    # Model status
    lines.append("# HELP truthlens_model_loaded Whether a model is loaded (1=yes, 0=no)")
    lines.append("# TYPE truthlens_model_loaded gauge")
    for modality, loaded in sorted(_model_loaded.items()):
        lines.append(f'truthlens_model_loaded{{modality="{modality}"}} {1 if loaded else 0}')

    return "\n".join(lines) + "\n"
