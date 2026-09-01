"""
Real-World Dataset & Benchmark Layer Service
Provides curated benchmark datasets, synthetic + real samples,
edge-case categories, annotation standards, and metrics reports.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class DatasetSample:
    """Single sample in a benchmark dataset."""
    sample_id: str
    modality: str  # text, image, audio, video
    label: str  # real, fake
    subcategory: str  # deepfake,GAN, edited, etc.
    difficulty: str  # easy, medium, hard, edge_case
    source: str
    metadata: dict = field(default_factory=dict)
    annotation: dict = field(default_factory=dict)


@dataclass
class BenchmarkDataset:
    """A curated benchmark dataset."""
    dataset_id: str
    name: str
    description: str
    modality: str
    total_samples: int
    real_samples: int
    fake_samples: int
    categories: dict = field(default_factory=dict)
    difficulty_distribution: dict = field(default_factory=dict)
    annotation_standards: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class MetricsReport:
    """Metrics report for a model on a dataset."""
    report_id: str
    model_name: str
    dataset_name: str
    overall_accuracy: float
    per_class_metrics: dict
    per_category_metrics: dict
    per_difficulty_metrics: dict
    confusion_matrix: list
    roc_auc: float
    average_precision: float
    timestamp: str


class BenchmarkDatasetService:
    """Manages benchmark datasets and evaluation."""
    
    def __init__(self):
        self.datasets = {}
        self.evaluation_results = []
        self.annotation_standards = self._load_annotation_standards()
    
    def create_dataset(self, name: str, description: str, modality: str,
                      samples: list = None) -> BenchmarkDataset:
        """Create a new benchmark dataset."""
        dataset_id = str(uuid.uuid4())
        
        samples = samples or []
        real_samples = sum(1 for s in samples if s.get("label") == "real")
        fake_samples = sum(1 for s in samples if s.get("label") == "fake")
        
        # Calculate categories
        categories = defaultdict(int)
        difficulty_dist = defaultdict(int)
        
        for sample in samples:
            categories[sample.get("subcategory", "unknown")] += 1
            difficulty_dist[sample.get("difficulty", "medium")] += 1
        
        dataset = BenchmarkDataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            modality=modality,
            total_samples=len(samples),
            real_samples=real_samples,
            fake_samples=fake_samples,
            categories=dict(categories),
            difficulty_distribution=dict(difficulty_dist),
            annotation_standards=self.annotation_standards.get(modality, {}),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        
        self.datasets[dataset_id] = {
            "dataset": dataset,
            "samples": samples,
        }
        
        return dataset
    
    def add_sample(self, dataset_id: str, sample: dict) -> dict:
        """Add a sample to a dataset."""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        sample_entry = DatasetSample(
            sample_id=str(uuid.uuid4()),
            modality=sample.get("modality", "unknown"),
            label=sample.get("label", "unknown"),
            subcategory=sample.get("subcategory", "unknown"),
            difficulty=sample.get("difficulty", "medium"),
            source=sample.get("source", "unknown"),
            metadata=sample.get("metadata", {}),
            annotation=sample.get("annotation", {}),
        )
        
        self.datasets[dataset_id]["samples"].append(sample)
        
        # Update dataset statistics
        dataset = self.datasets[dataset_id]["dataset"]
        dataset.total_samples += 1
        if sample.get("label") == "real":
            dataset.real_samples += 1
        elif sample.get("label") == "fake":
            dataset.fake_samples += 1
        
        # Update categories
        subcategory = sample.get("subcategory", "unknown")
        dataset.categories[subcategory] = dataset.categories.get(subcategory, 0) + 1
        
        # Update difficulty
        difficulty = sample.get("difficulty", "medium")
        dataset.difficulty_distribution[difficulty] = dataset.difficulty_distribution.get(difficulty, 0) + 1
        
        dataset.updated_at = datetime.now(timezone.utc).isoformat()
        
        return {"sample_id": sample_entry.sample_id, "status": "added"}
    
    def evaluate_model(self, dataset_id: str, model_name: str,
                      predictions: list) -> MetricsReport:
        """Evaluate a model on a dataset."""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        dataset_info = self.datasets[dataset_id]
        samples = dataset_info["samples"]
        
        # Match predictions to samples
        correct = 0
        total = len(predictions)
        class_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
        category_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
        difficulty_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
        confusion_matrix = [[0, 0], [0, 0]]  # [TN, FP], [FN, TP]
        
        for i, pred in enumerate(predictions):
            if i >= len(samples):
                break
            
            sample = samples[i]
            predicted_label = pred.get("label", "unknown")
            actual_label = sample.get("label", "unknown")
            
            if predicted_label == actual_label:
                correct += 1
                if actual_label == "fake":
                    confusion_matrix[1][1] += 1  # TP
                else:
                    confusion_matrix[0][0] += 1  # TN
            else:
                if predicted_label == "fake" and actual_label == "real":
                    confusion_matrix[0][1] += 1  # FP
                else:
                    confusion_matrix[1][0] += 1  # FN
            
            # Per-class metrics
            class_metrics[actual_label]["total"] += 1
            if predicted_label == actual_label:
                class_metrics[actual_label]["correct"] += 1
            
            # Per-category metrics
            category = sample.get("subcategory", "unknown")
            category_metrics[category]["total"] += 1
            if predicted_label == actual_label:
                category_metrics[category]["correct"] += 1
            
            # Per-difficulty metrics
            difficulty = sample.get("difficulty", "medium")
            difficulty_metrics[difficulty]["total"] += 1
            if predicted_label == actual_label:
                difficulty_metrics[difficulty]["correct"] += 1
        
        # Calculate overall accuracy
        accuracy = correct / total if total > 0 else 0
        
        # Calculate per-class metrics
        per_class = {}
        for label, metrics in class_metrics.items():
            per_class[label] = {
                "accuracy": metrics["correct"] / max(metrics["total"], 1),
                "total": metrics["total"],
                "correct": metrics["correct"],
            }
        
        # Calculate per-category metrics
        per_category = {}
        for category, metrics in category_metrics.items():
            per_category[category] = {
                "accuracy": metrics["correct"] / max(metrics["total"], 1),
                "total": metrics["total"],
                "correct": metrics["correct"],
            }
        
        # Calculate per-difficulty metrics
        per_difficulty = {}
        for difficulty, metrics in difficulty_metrics.items():
            per_difficulty[difficulty] = {
                "accuracy": metrics["correct"] / max(metrics["total"], 1),
                "total": metrics["total"],
                "correct": metrics["correct"],
            }
        
        # Calculate ROC AUC (simplified)
        roc_auc = self._calculate_roc_auc(predictions, samples)
        
        # Calculate Average Precision (simplified)
        avg_precision = self._calculate_average_precision(predictions, samples)
        
        report = MetricsReport(
            report_id=str(uuid.uuid4()),
            model_name=model_name,
            dataset_name=dataset_info["dataset"].name,
            overall_accuracy=accuracy,
            per_class_metrics=per_class,
            per_category_metrics=per_category,
            per_difficulty_metrics=per_difficulty,
            confusion_matrix=confusion_matrix,
            roc_auc=roc_auc,
            average_precision=avg_precision,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        self.evaluation_results.append(report)
        return report
    
    def get_dataset_summary(self, dataset_id: str) -> dict:
        """Get summary of a dataset."""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        dataset = self.datasets[dataset_id]["dataset"]
        
        return {
            "dataset_id": dataset.dataset_id,
            "name": dataset.name,
            "description": dataset.description,
            "modality": dataset.modality,
            "total_samples": dataset.total_samples,
            "real_samples": dataset.real_samples,
            "fake_samples": dataset.fake_samples,
            "categories": dataset.categories,
            "difficulty_distribution": dataset.difficulty_distribution,
            "annotation_standards": dataset.annotation_standards,
        }
    
    def get_evaluation_summary(self) -> list:
        """Get summary of all evaluation results."""
        return [
            {
                "report_id": r.report_id,
                "model_name": r.model_name,
                "dataset_name": r.dataset_name,
                "accuracy": r.overall_accuracy,
                "roc_auc": r.roc_auc,
                "timestamp": r.timestamp,
            }
            for r in self.evaluation_results
        ]
    
    def _calculate_roc_auc(self, predictions: list, samples: list) -> float:
        """Calculate ROC AUC score (simplified)."""
        if not predictions or not samples:
            return 0.5
        
        # Simplified ROC AUC calculation
        # In production, use sklearn.metrics.roc_auc_score
        scores = []
        labels = []
        
        for i, pred in enumerate(predictions):
            if i >= len(samples):
                break
            score = pred.get("confidence", 0.5)
            label = 1 if samples[i].get("label") == "fake" else 0
            scores.append(score)
            labels.append(label)
        
        # Simple AUC calculation
        if len(set(labels)) < 2:
            return 0.5
        
        # Sort by score
        sorted_pairs = sorted(zip(scores, labels), key=lambda x: x[0], reverse=True)
        
        tp = 0
        fp = 0
        total_pos = sum(labels)
        total_neg = len(labels) - total_pos
        
        auc = 0.0
        for score, label in sorted_pairs:
            if label == 1:
                tp += 1
            else:
                fp += 1
                auc += tp / total_pos
        
        auc = auc / (total_pos * total_neg) if total_pos * total_neg > 0 else 0.5
        return auc
    
    def _calculate_average_precision(self, predictions: list, samples: list) -> float:
        """Calculate Average Precision (simplified)."""
        if not predictions or not samples:
            return 0.0
        
        # Simplified AP calculation
        # In production, use sklearn.metrics.average_precision_score
        sorted_pairs = sorted(
            zip(
                [p.get("confidence", 0.5) for p in predictions[:len(samples)]],
                [1 if s.get("label") == "fake" else 0 for s in samples[:len(predictions)]],
            ),
            key=lambda x: x[0],
            reverse=True,
        )
        
        tp = 0
        fp = 0
        total_pos = sum(label for _, label in sorted_pairs)
        
        ap = 0.0
        for score, label in sorted_pairs:
            if label == 1:
                tp += 1
                ap += tp / (tp + fp)
            else:
                fp += 1
        
        ap = ap / total_pos if total_pos > 0 else 0.0
        return ap
    
    def _load_annotation_standards(self) -> dict:
        """Load annotation standards for each modality."""
        return {
            "text": {
                "label_definitions": {
                    "real": "Content that is factually accurate and not manipulated",
                    "fake": "Content that contains false information or is intentionally misleading",
                },
                "annotation_criteria": [
                    "Source verification",
                    "Fact-check alignment",
                    "Emotional manipulation detection",
                    "Bias assessment",
                ],
                "difficulty_levels": {
                    "easy": "Obvious misinformation with clear indicators",
                    "medium": "Subtle manipulation requiring careful analysis",
                    "hard": "Sophisticated manipulation that mimics real content",
                    "edge_case": "Ambiguous content that experts disagree on",
                },
            },
            "image": {
                "label_definitions": {
                    "real": "Image that has not been digitally manipulated",
                    "fake": "Image that has been altered, generated, or deepfaked",
                },
                "annotation_criteria": [
                    "Frequency domain analysis",
                    "Metadata consistency",
                    "Visual artifact detection",
                    "Source verification",
                ],
                "difficulty_levels": {
                    "easy": "Obvious manipulation with visible artifacts",
                    "medium": "Subtle manipulation requiring forensic analysis",
                    "hard": "High-quality deepfake with minimal artifacts",
                    "edge_case": "Legitimate image with unusual characteristics",
                },
            },
            "audio": {
                "label_definitions": {
                    "real": "Audio that is authentic and not synthesized",
                    "fake": "Audio that is cloned, generated, or manipulated",
                },
                "annotation_criteria": [
                    "Voice clone detection",
                    "Spectral analysis",
                    "Temporal consistency",
                    "Background noise analysis",
                ],
                "difficulty_levels": {
                    "easy": "Obvious synthesis with robotic artifacts",
                    "medium": "High-quality clone with subtle artifacts",
                    "hard": "Advanced clone that passes most detectors",
                    "edge_case": "Audio with unusual recording conditions",
                },
            },
            "video": {
                "label_definitions": {
                    "real": "Video that is authentic and not manipulated",
                    "fake": "Video that is deepfaked, edited, or generated",
                },
                "annotation_criteria": [
                    "Face swap detection",
                    "Lip sync analysis",
                    "Temporal consistency",
                    "Metadata verification",
                ],
                "difficulty_levels": {
                    "easy": "Obvious face swap with artifacts",
                    "medium": "High-quality deepfake with subtle issues",
                    "hard": "Advanced deepfake that passes most detectors",
                    "edge_case": "Video with unusual lighting or angles",
                },
            },
        }


# Singleton instance
_benchmark_service = None


def get_benchmark_service() -> BenchmarkDatasetService:
    """Get or create singleton benchmark dataset service."""
    global _benchmark_service
    if _benchmark_service is None:
        _benchmark_service = BenchmarkDatasetService()
    return _benchmark_service
