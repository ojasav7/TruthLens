"""Model Benchmark — tracks performance metrics per model version. ponytail: JSON file store."""

import json
import os
from pathlib import Path

BENCHMARK_FILE = Path("data/benchmarks.json")


def _load() -> dict:
    if BENCHMARK_FILE.exists():
        return json.loads(BENCHMARK_FILE.read_text())
    return {}


def _save(data: dict):
    BENCHMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_FILE.write_text(json.dumps(data, indent=2))


def record_benchmark(modality: str, version: str, metrics: dict):
    """Record benchmark results for a model version."""
    data = _load()
    data.setdefault(modality, {})[version] = metrics
    _save(data)


def get_benchmarks(modality: str | None = None) -> dict:
    data = _load()
    if modality:
        return {modality: data.get(modality, {})}
    return data


def get_versions() -> dict:
    """Get all model versions across all modalities."""
    from backend.services.investigation_service import MODEL_VERSIONS
    data = _load()
    result = {}
    for mod, ver in MODEL_VERSIONS.items():
        benchmarks = data.get(mod, {}).get(ver, {})
        result[mod] = {"version": ver, "benchmarks": benchmarks}
    return result


# Seed default benchmarks if empty
if not BENCHMARK_FILE.exists():
    _save({
        "nlp": {"1.0.0": {"accuracy": 1.0, "f1": 1.0, "precision": 1.0, "recall": 1.0}},
        "image": {"1.0.0": {"accuracy": 0.66, "f1": 0.65, "precision": 0.67, "recall": 0.64}},
        "video": {"1.0.0": {"accuracy": 1.0, "f1": 1.0, "precision": 1.0, "recall": 1.0}},
        "audio": {"1.0.0": {"accuracy": 1.0, "f1": 1.0, "precision": 1.0, "recall": 1.0}},
    })
