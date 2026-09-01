"""
Model Calibration & Benchmarking Dashboard Service
Provides calibration curves, confidence distribution, false positive/negative tracking,
per-modality performance, and benchmark dataset summary.
"""

import time
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class CalibrationDataPoint:
    """Single calibration data point."""
    predicted_confidence: float
    actual_outcome: bool  # True = correct, False = incorrect
    modality: str
    timestamp: str


@dataclass
class ModalityPerformance:
    """Performance metrics for a single modality."""
    modality: str
    total_predictions: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    true_positives: int
    true_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_confidence: float
    calibration_error: float


@dataclass
class BenchmarkResult:
    """Results from benchmark dataset evaluation."""
    dataset_name: str
    total_samples: int
    correct: int
    accuracy: float
    per_class_metrics: dict
    per_modality_metrics: dict
    confusion_matrix: list
    timestamp: str


@dataclass
class CalibrationDashboardResult:
    """Complete calibration dashboard data."""
    calibration_curve: list
    confidence_distribution: list
    modality_performance: list
    overall_performance: dict
    false_positive_rate: float
    false_negative_rate: float
    benchmark_results: list
    timestamp: str


class CalibrationDashboard:
    """Manages model calibration and benchmarking."""
    
    def __init__(self):
        self.calibration_data = []
        self.prediction_log = []
        self.benchmark_results = []
    
    def record_prediction(self, modality: str, predicted_confidence: float,
                         actual_outcome: bool, prediction: dict):
        """Record a prediction for calibration tracking."""
        data_point = CalibrationDataPoint(
            predicted_confidence=predicted_confidence,
            actual_outcome=actual_outcome,
            modality=modality,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        self.calibration_data.append(data_point)
        
        self.prediction_log.append({
            "modality": modality,
            "predicted_confidence": predicted_confidence,
            "actual_outcome": actual_outcome,
            "prediction": prediction,
            "timestamp": data_point.timestamp,
        })
    
    def get_calibration_curve(self, n_bins: int = 10) -> list:
        """Calculate calibration curve data points."""
        if not self.calibration_data:
            return []
        
        # Sort by confidence
        sorted_data = sorted(self.calibration_data, key=lambda x: x.predicted_confidence)
        
        # Create bins
        bin_size = max(1, len(sorted_data) // n_bins)
        calibration_points = []
        
        for i in range(0, len(sorted_data), bin_size):
            bin_data = sorted_data[i:i + bin_size]
            if not bin_data:
                continue
            
            avg_confidence = sum(d.predicted_confidence for d in bin_data) / len(bin_data)
            actual_accuracy = sum(1 for d in bin_data if d.actual_outcome) / len(bin_data)
            
            calibration_points.append({
                "predicted": round(avg_confidence, 3),
                "actual": round(actual_accuracy, 3),
                "count": len(bin_data),
            })
        
        return calibration_points
    
    def get_confidence_distribution(self) -> list:
        """Get distribution of confidence scores."""
        if not self.calibration_data:
            return []
        
        # Create histogram
        bins = [0] * 10  # 0-10%, 10-20%, ..., 90-100%
        
        for data_point in self.calibration_data:
            bin_index = min(int(data_point.predicted_confidence * 10), 9)
            bins[bin_index] += 1
        
        total = len(self.calibration_data)
        
        return [
            {
                "range": f"{i * 10}%-{(i + 1) * 10}%",
                "count": bins[i],
                "percentage": round(bins[i] / total * 100, 1) if total > 0 else 0,
            }
            for i in range(10)
        ]
    
    def get_modality_performance(self) -> list:
        """Calculate per-modality performance metrics."""
        modality_data = defaultdict(list)
        
        for data_point in self.calibration_data:
            modality_data[data_point.modality].append(data_point)
        
        performance = []
        
        for modality, data_points in modality_data.items():
            metrics = self._calculate_modality_metrics(modality, data_points)
            performance.append(metrics)
        
        return performance
    
    def get_overall_performance(self) -> dict:
        """Calculate overall performance metrics."""
        if not self.calibration_data:
            return {
                "total_predictions": 0,
                "accuracy": 0,
                "precision": 0,
                "recall": 0,
                "f1_score": 0,
                "avg_confidence": 0,
            }
        
        total = len(self.calibration_data)
        correct = sum(1 for d in self.calibration_data if d.actual_outcome)
        
        # Calculate precision and recall (simplified)
        true_positives = sum(1 for d in self.calibration_data 
                           if d.actual_outcome and d.predicted_confidence > 0.5)
        false_positives = sum(1 for d in self.calibration_data 
                            if not d.actual_outcome and d.predicted_confidence > 0.5)
        false_negatives = sum(1 for d in self.calibration_data 
                            if d.actual_outcome and d.predicted_confidence <= 0.5)
        
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1_score = 2 * precision * recall / max(precision + recall, 0.001)
        
        avg_confidence = sum(d.predicted_confidence for d in self.calibration_data) / total
        
        return {
            "total_predictions": total,
            "accuracy": round(correct / total, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "avg_confidence": round(avg_confidence, 3),
        }
    
    def get_false_positive_negative_rates(self) -> dict:
        """Calculate false positive and false negative rates."""
        if not self.calibration_data:
            return {"false_positive_rate": 0, "false_negative_rate": 0}
        
        false_positives = sum(1 for d in self.calibration_data 
                            if not d.actual_outcome and d.predicted_confidence > 0.5)
        false_negatives = sum(1 for d in self.calibration_data 
                            if d.actual_outcome and d.predicted_confidence <= 0.5)
        
        total_negative = sum(1 for d in self.calibration_data if not d.actual_outcome)
        total_positive = sum(1 for d in self.calibration_data if d.actual_outcome)
        
        fpr = false_positives / max(total_negative, 1)
        fnr = false_negatives / max(total_positive, 1)
        
        return {
            "false_positive_rate": round(fpr, 3),
            "false_negative_rate": round(fnr, 3),
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        }
    
    def run_benchmark(self, dataset_name: str, test_data: list) -> BenchmarkResult:
        """Run benchmark evaluation on test dataset."""
        correct = 0
        total = len(test_data)
        class_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
        confusion_matrix = [[0, 0], [0, 0]]  # [TN, FP], [FN, TP]
        
        for sample in test_data:
            predicted = sample.get("predicted_label", "unknown")
            actual = sample.get("actual_label", "unknown")
            
            if predicted == actual:
                correct += 1
                if actual == "fake":
                    confusion_matrix[1][1] += 1  # TP
                else:
                    confusion_matrix[0][0] += 1  # TN
            else:
                if predicted == "fake" and actual == "real":
                    confusion_matrix[0][1] += 1  # FP
                else:
                    confusion_matrix[1][0] += 1  # FN
            
            class_metrics[actual]["total"] += 1
            if predicted == actual:
                class_metrics[actual]["correct"] += 1
        
        accuracy = correct / total if total > 0 else 0
        
        per_class = {}
        for label, metrics in class_metrics.items():
            per_class[label] = {
                "accuracy": metrics["correct"] / max(metrics["total"], 1),
                "total": metrics["total"],
                "correct": metrics["correct"],
            }
        
        result = BenchmarkResult(
            dataset_name=dataset_name,
            total_samples=total,
            correct=correct,
            accuracy=accuracy,
            per_class_metrics=per_class,
            per_modality_metrics={},
            confusion_matrix=confusion_matrix,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        self.benchmark_results.append(result)
        return result
    
    def get_benchmark_summary(self) -> list:
        """Get summary of all benchmark results."""
        return [
            {
                "dataset": r.dataset_name,
                "accuracy": r.accuracy,
                "total_samples": r.total_samples,
                "correct": r.correct,
                "timestamp": r.timestamp,
            }
            for r in self.benchmark_results
        ]
    
    def get_dashboard_data(self) -> CalibrationDashboardResult:
        """Get complete dashboard data."""
        return CalibrationDashboardResult(
            calibration_curve=self.get_calibration_curve(),
            confidence_distribution=self.get_confidence_distribution(),
            modality_performance=self.get_modality_performance(),
            overall_performance=self.get_overall_performance(),
            false_positive_rate=self.get_false_positive_negative_rates()["false_positive_rate"],
            false_negative_rate=self.get_false_positive_negative_rates()["false_negative_rate"],
            benchmark_results=self.get_benchmark_summary(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    def _calculate_modality_metrics(self, modality: str, data_points: list) -> dict:
        """Calculate metrics for a single modality."""
        total = len(data_points)
        correct = sum(1 for d in data_points if d.actual_outcome)
        
        true_positives = sum(1 for d in data_points 
                           if d.actual_outcome and d.predicted_confidence > 0.5)
        false_positives = sum(1 for d in data_points 
                            if not d.actual_outcome and d.predicted_confidence > 0.5)
        false_negatives = sum(1 for d in data_points 
                            if d.actual_outcome and d.predicted_confidence <= 0.5)
        true_negatives = sum(1 for d in data_points 
                           if not d.actual_outcome and d.predicted_confidence <= 0.5)
        
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1_score = 2 * precision * recall / max(precision + recall, 0.001)
        avg_confidence = sum(d.predicted_confidence for d in data_points) / total
        
        # Calculate calibration error
        calibration_error = self._calculate_calibration_error(data_points)
        
        return {
            "modality": modality,
            "total_predictions": total,
            "correct_predictions": correct,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_positives": true_positives,
            "true_negatives": true_negatives,
            "accuracy": round(correct / total, 3) if total > 0 else 0,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "avg_confidence": round(avg_confidence, 3),
            "calibration_error": round(calibration_error, 3),
        }
    
    def _calculate_calibration_error(self, data_points: list) -> float:
        """Calculate Expected Calibration Error (ECE)."""
        if not data_points:
            return 0.0
        
        # Sort by confidence
        sorted_data = sorted(data_points, key=lambda x: x.predicted_confidence)
        
        n_bins = min(10, len(sorted_data))
        bin_size = max(1, len(sorted_data) // n_bins)
        
        ece = 0.0
        for i in range(0, len(sorted_data), bin_size):
            bin_data = sorted_data[i:i + bin_size]
            if not bin_data:
                continue
            
            avg_confidence = sum(d.predicted_confidence for d in bin_data) / len(bin_data)
            actual_accuracy = sum(1 for d in bin_data if d.actual_outcome) / len(bin_data)
            
            ece += abs(avg_confidence - actual_accuracy) * len(bin_data) / len(sorted_data)
        
        return ece


# Singleton instance
_calibration_dashboard = None


def get_calibration_dashboard() -> CalibrationDashboard:
    """Get or create singleton calibration dashboard."""
    global _calibration_dashboard
    if _calibration_dashboard is None:
        _calibration_dashboard = CalibrationDashboard()
    return _calibration_dashboard
