"""Evidence Graph — builds nodes + edges from evidence records and relations."""


async def build_graph(case_id: str) -> dict:
    """Build a graph representation of evidence for a case."""
    from backend.db.database import async_session
    from backend.db.models_advanced import Evidence, EvidenceRelation, InvestigationCase
    from sqlalchemy import select

    async with async_session() as session:
        # Get case
        case_r = await session.execute(select(InvestigationCase).where(InvestigationCase.id == case_id))
        case = case_r.scalar_one_or_none()
        if not case:
            return {"error": "Case not found"}

        # Get evidence nodes
        ev_r = await session.execute(select(Evidence).where(Evidence.case_id == case_id))
        evidence = ev_r.scalars().all()

        # Get relations
        rel_r = await session.execute(select(EvidenceRelation).where(EvidenceRelation.case_id == case_id))
        relations = rel_r.scalars().all()

    # Build nodes
    nodes = []
    for e in evidence:
        nodes.append({
            "id": e.id, "type": e.type, "module": e.source_module,
            "description": e.description, "score": e.score,
            "impact": e.impact, "category": e.category,
        })

    # Build edges
    edges = []
    for r in relations:
        edges.append({
            "source": r.source_evidence_id, "target": r.target_evidence_id,
            "relation": r.relation_type,
        })

    # Auto-generate standard edges if none exist
    if not edges and len(nodes) >= 2:
        edges = _auto_generate_edges(nodes)

    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


def _auto_generate_edges(nodes: list[dict]) -> list[dict]:
    """Auto-generate graph edges from evidence types."""
    edges = []
    evidence_map = {n["id"]: n for n in nodes}

    for i, n1 in enumerate(nodes):
        for n2 in nodes[i + 1:]:
            # Contradicting evidence
            if n1.get("category") == "SUPPORTING" and n2.get("category") == "NEUTRAL":
                edges.append({"source": n1["id"], "target": n2["id"], "relation": "CONTRADICTS"})
            elif n1.get("category") == n2.get("category") and n1["category"] != "NEUTRAL":
                edges.append({"source": n1["id"], "target": n2["id"], "relation": "SUPPORTS"})
            # Different modalities → cross-modal signal
            if n1.get("module") != n2.get("module"):
                edges.append({"source": n1["id"], "target": n2["id"], "relation": "CROSS_MODAL_SIGNAL"})

    return edges


async def add_relation(case_id: str, source_id: str, target_id: str, relation_type: str) -> dict:
    from backend.db.database import async_session
    from backend.db.models_advanced import EvidenceRelation
    rel = EvidenceRelation(case_id=case_id, source_evidence_id=source_id, target_evidence_id=target_id, relation_type=relation_type)
    async with async_session() as session:
        session.add(rel)
        await session.commit()
    return {"status": "added", "relation": relation_type}
