"""SQLite persistence for advanced features. stdlib only."""

import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.getenv("TRUTHLENS_DB", "truthlens_advanced.db")

_conn = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript("""
            CREATE TABLE IF NOT EXISTS review_workflows (
                analysis_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS calibration_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modality TEXT NOT NULL,
                confidence REAL NOT NULL,
                correct INTEGER NOT NULL,
                recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset TEXT NOT NULL,
                accuracy REAL NOT NULL,
                total INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                recorded_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                details TEXT,
                recorded_at TEXT NOT NULL
            );
        """)
    return _conn


def save_workflow(analysis_id: str, data: dict):
    _get_conn().execute(
        "INSERT OR REPLACE INTO review_workflows (analysis_id, data, updated_at) VALUES (?, ?, ?)",
        (analysis_id, json.dumps(data), datetime.now(timezone.utc).isoformat()),
    )
    _get_conn().commit()


def load_workflow(analysis_id: str) -> dict | None:
    row = _get_conn().execute(
        "SELECT data FROM review_workflows WHERE analysis_id = ?", (analysis_id,)
    ).fetchone()
    return json.loads(row["data"]) if row else None


def load_all_workflows() -> list:
    rows = _get_conn().execute("SELECT data FROM review_workflows").fetchall()
    return [json.loads(r["data"]) for r in rows]


def save_prediction(modality: str, confidence: float, correct: bool):
    _get_conn().execute(
        "INSERT INTO calibration_predictions (modality, confidence, correct, recorded_at) VALUES (?, ?, ?, ?)",
        (modality, confidence, int(correct), datetime.now(timezone.utc).isoformat()),
    )
    _get_conn().commit()


def load_predictions() -> list:
    rows = _get_conn().execute("SELECT modality, confidence, correct FROM calibration_predictions").fetchall()
    return [{"modality": r["modality"], "confidence": r["confidence"], "correct": bool(r["correct"])} for r in rows]


def save_benchmark(dataset: str, accuracy: float, total: int, correct: int):
    _get_conn().execute(
        "INSERT INTO benchmark_runs (dataset, accuracy, total, correct, recorded_at) VALUES (?, ?, ?, ?, ?)",
        (dataset, accuracy, total, correct, datetime.now(timezone.utc).isoformat()),
    )
    _get_conn().commit()


def load_benchmarks() -> list:
    rows = _get_conn().execute("SELECT dataset, accuracy, total, correct FROM benchmark_runs").fetchall()
    return [{"dataset": r["dataset"], "accuracy": r["accuracy"], "total_samples": r["total"], "correct": r["correct"]} for r in rows]


def save_timeline_event(content_id: str, event_type: str, source: str, details: dict = None):
    _get_conn().execute(
        "INSERT INTO timeline_events (content_id, event_type, source, details, recorded_at) VALUES (?, ?, ?, ?, ?)",
        (content_id, event_type, source, json.dumps(details or {}), datetime.now(timezone.utc).isoformat()),
    )
    _get_conn().commit()


def load_timeline(content_id: str) -> list:
    rows = _get_conn().execute(
        "SELECT event_type, source, details, recorded_at FROM timeline_events WHERE content_id = ? ORDER BY recorded_at",
        (content_id,),
    ).fetchall()
    return [{"event_type": r["event_type"], "source": r["source"], "details": json.loads(r["details"]), "timestamp": r["recorded_at"]} for r in rows]
