"""Calibration & Benchmark — tracking predictions and model evaluation. SQLite-backed."""

from collections import defaultdict
from backend.services.db_persist import save_prediction, load_predictions, save_benchmark, load_benchmarks


def record_prediction(modality: str, confidence: float, correct: bool):
    save_prediction(modality, confidence, correct)


def get_calibration_curve(n_bins: int = 10) -> list:
    preds = load_predictions()
    if not preds:
        return []
    sorted_p = sorted(preds, key=lambda x: x["confidence"])
    bin_size = max(1, len(sorted_p) // n_bins)
    points = []
    for i in range(0, len(sorted_p), bin_size):
        bin_data = sorted_p[i:i + bin_size]
        avg_conf = sum(d["confidence"] for d in bin_data) / len(bin_data)
        actual_acc = sum(1 for d in bin_data if d["correct"]) / len(bin_data)
        points.append({"predicted": round(avg_conf, 3), "actual": round(actual_acc, 3), "count": len(bin_data)})
    return points


def get_modality_performance() -> dict:
    preds = load_predictions()
    by_mod = defaultdict(list)
    for p in preds:
        by_mod[p["modality"]].append(p)
    result = {}
    for mod, ps in by_mod.items():
        total = len(ps)
        correct = sum(1 for p in ps if p["correct"])
        result[mod] = {"accuracy": round(correct / total, 3), "total": total, "correct": correct}
    return result


def get_dashboard() -> dict:
    preds = load_predictions()
    total = len(preds)
    correct = sum(1 for p in preds if p["correct"])
    return {
        "overall_accuracy": round(correct / total, 3) if total else 0,
        "total_predictions": total,
        "calibration_curve": get_calibration_curve(),
        "modality_performance": get_modality_performance(),
        "benchmark_results": load_benchmarks(),
    }


def run_benchmark(dataset_name: str, samples: list) -> dict:
    correct = sum(1 for s in samples if s.get("predicted") == s.get("actual"))
    accuracy = correct / len(samples) if samples else 0
    save_benchmark(dataset_name, accuracy, len(samples), correct)
    return {"dataset": dataset_name, "accuracy": round(accuracy, 3), "total_samples": len(samples), "correct": correct}
