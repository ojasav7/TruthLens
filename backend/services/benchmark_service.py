"""Benchmark Dataset Layer — labeled samples, per-modality metrics, false-positive tracking. SQLite-backed."""

import json
from backend.services.db_persist import save_benchmark, load_benchmarks


# === Benchmark Datasets ===
# Labeled real/synthetic samples for evaluation

DATASETS = {
    "text": {
        "name": "Text Misinformation Detection",
        "samples": [
            {"id": "t1", "text": "NASA confirms earth will be destroyed by asteroid in 2026", "label": "fake", "category": "sensationalism"},
            {"id": "t2", "text": "Climate change is real according to NASA research", "label": "real", "category": "scientific"},
            {"id": "t3", "text": "5G towers cause cancer according to new study", "label": "fake", "category": "conspiracy"},
            {"id": "t4", "text": "WHO approves new vaccine for malaria", "label": "real", "category": "health"},
            {"id": "t5", "text": "Flat earth proven by NASA whistleblower", "label": "fake", "category": "conspiracy"},
            {"id": "t6", "text": "Stock market closes at record high amid economic recovery", "label": "real", "category": "finance"},
            {"id": "t7", "text": "Celebrity death hoax spreads on social media", "label": "fake", "category": "hoax"},
            {"id": "t8", "text": "New study finds link between exercise and brain health", "label": "real", "category": "health"},
            {"id": "t9", "text": "Government secretly controlling weather with chemtrails", "label": "fake", "category": "conspiracy"},
            {"id": "t10", "text": "University researchers develop new antibiotic", "label": "real", "category": "science"},
        ],
    },
    "image": {
        "name": "Image Deepfake Detection",
        "samples": [
            {"id": "i1", "source": "ffpp_real", "label": "real", "category": "face_swap_real"},
            {"id": "i2", "source": "ffpp_deepfakes", "label": "fake", "category": "deepfake"},
            {"id": "i3", "source": "ffpp_face2face", "label": "fake", "category": "face2face"},
            {"id": "i4", "source": "ffpp_real", "label": "real", "category": "original"},
            {"id": "i5", "source": "ffpp_faceswap", "label": "fake", "category": "faceswap"},
        ],
    },
    "audio": {
        "name": "Audio Voice Clone Detection",
        "samples": [
            {"id": "a1", "source": "real_speech", "label": "real", "category": "natural"},
            {"id": "a2", "source": "cloned_speech", "label": "fake", "category": "voice_clone"},
            {"id": "a3", "source": "real_speech", "label": "real", "category": "natural"},
            {"id": "a4", "source": "tts_generated", "label": "fake", "category": "tts"},
            {"id": "a5", "source": "real_speech", "label": "real", "category": "natural"},
        ],
    },
    "video": {
        "name": "Video Deepfake Detection",
        "samples": [
            {"id": "v1", "source": "ffpp_real", "label": "real", "category": "original"},
            {"id": "v2", "source": "ffpp_deepfakes", "label": "fake", "category": "deepfake"},
            {"id": "v3", "source": "ffpp_real", "label": "real", "category": "original"},
            {"id": "v4", "source": "ffpp_deepfakes", "label": "fake", "category": "deepfake"},
            {"id": "v5", "source": "ffpp_real", "label": "real", "category": "original"},
        ],
    },
}


def get_datasets() -> dict:
    """Get all benchmark datasets with sample counts."""
    return {
        modality: {"name": ds["name"], "total_samples": len(ds["samples"]), "real": sum(1 for s in ds["samples"] if s["label"] == "real"), "fake": sum(1 for s in ds["samples"] if s["label"] == "fake")}
        for modality, ds in DATASETS.items()
    }


def get_samples(modality: str) -> list:
    """Get labeled samples for a modality."""
    ds = DATASETS.get(modality)
    return ds["samples"] if ds else []


def evaluate_predictions(modality: str, predictions: list[dict]) -> dict:
    """Evaluate model predictions against labeled samples.

    predictions: [{"id": "t1", "predicted": "fake"}, ...]
    Returns: accuracy, precision, recall, f1, false_positives, false_negatives
    """
    ds = DATASETS.get(modality)
    if not ds:
        return {"error": f"Unknown modality: {modality}"}

    # Map predictions by id
    pred_map = {p["id"]: p.get("predicted", "unknown") for p in predictions}

    tp = fp = tn = fn = 0
    per_sample = []

    for sample in ds["samples"]:
        sid = sample["id"]
        actual = sample["label"]
        predicted = pred_map.get(sid, "unknown")

        if actual == "fake" and predicted == "fake":
            tp += 1
            outcome = "true_positive"
        elif actual == "real" and predicted == "real":
            tn += 1
            outcome = "true_negative"
        elif actual == "real" and predicted == "fake":
            fp += 1
            outcome = "false_positive"
        else:
            fn += 1
            outcome = "false_negative"

        per_sample.append({"id": sid, "actual": actual, "predicted": predicted, "outcome": outcome, "category": sample.get("category", "")})

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    result = {
        "modality": modality,
        "dataset": ds["name"],
        "total_samples": total,
        "accuracy": round(accuracy, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "false_positives": fp,
        "false_negatives": fn,
        "per_sample": per_sample,
    }

    # Persist to SQLite
    save_benchmark(ds["name"], accuracy, total, tp + tn)
    return result


def get_modality_metrics() -> dict:
    """Get per-modality performance from persisted benchmarks."""
    benchmarks = load_benchmarks()
    by_modality = {}
    for b in benchmarks:
        by_modality[b["dataset"]] = {"accuracy": b["accuracy"], "total_samples": b["total"], "correct": b["correct"]}
    return by_modality


def get_false_positive_rate(modality: str) -> dict:
    """Get false positive rate for a modality from latest benchmark."""
    benchmarks = load_benchmarks()
    for b in reversed(benchmarks):
        if b["dataset"].lower().startswith(modality.lower()):
            accuracy = b["accuracy"]
            return {"modality": modality, "accuracy": accuracy, "estimated_fpr": round(1 - accuracy, 3)}
    return {"modality": modality, "accuracy": None, "estimated_fpr": None}
