"""Evidence Dependency Graph.

Shows how evidence contributes to conclusions. Supports:
supports, contradicts, derived_from, associated_with, corroborates, depends_on.
"""

import logging
from dataclasses import asdict

logger = logging.getLogger("truthlens.dependency")


def build_dependency_graph(evidence_items: list[dict], sources: list[dict] | None = None, model_signals: list[dict] | None = None, conclusion: dict | None = None) -> dict:
    nodes, edges = [], []

    for ev in evidence_items:
        nodes.append({"id": ev.get("id", "?"), "type": "evidence", "label": ev.get("description", ev.get("type", "evidence"))[:60]})

    for src in (sources or []):
        nodes.append({"id": src.get("id", "?"), "type": "source", "label": src.get("name", "source")[:60]})
        for ev_id in src.get("evidence_ids", []):
            edges.append({"source": src["id"], "target": ev_id, "relation": "derived_from"})

    for sig in (model_signals or []):
        nodes.append({"id": sig.get("id", "?"), "type": "model_signal", "label": f"{sig.get('modality', '?')}: {sig.get('label', '?')}"})

    if conclusion:
        nodes.append({"id": "conclusion", "type": "conclusion", "label": f"Assessment: {conclusion.get('verdict', '?')}"})
        for ev in evidence_items:
            rel = "supports" if ev.get("category", "NEUTRAL") in ("POSITIVE", "NEUTRAL") else "contradicts"
            edges.append({"source": ev.get("id", "?"), "target": "conclusion", "relation": rel, "weight": abs(ev.get("score", 0.5))})

    # ponytail: O(n²) redundancy check is fine for <100 evidence items. Add index if count grows.
    src_evidence_count = {}
    for e in edges:
        if e["relation"] == "derived_from":
            src_evidence_count[e["source"]] = src_evidence_count.get(e["source"], 0) + 1
    redundant = {s: c for s, c in src_evidence_count.items() if c >= 3}

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {"total_nodes": len(nodes), "total_edges": len(edges), "supports": sum(1 for e in edges if e["relation"] == "supports"), "contradicts": sum(1 for e in edges if e["relation"] == "contradicts"), "redundant_sources": redundant},
    }


def query_dependency(graph: dict, evidence_id: str) -> dict:
    edges = graph["edges"]
    return {
        "evidence_id": evidence_id,
        "supports": [e["target"] for e in edges if e["source"] == evidence_id and e["relation"] == "supports"],
        "contradicts": [e["target"] for e in edges if e["source"] == evidence_id and e["relation"] == "contradicts"],
        "depends_on": [e["source"] for e in edges if e["target"] == evidence_id and e["relation"] == "depends_on"],
    }
