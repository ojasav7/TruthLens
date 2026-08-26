"""Misinformation Radar — aggregate analytics. ponytail: simple SQL aggregations."""

from backend.db.database import async_session
from backend.db.models import Analysis
from sqlalchemy import select, func


async def get_radar() -> dict:
    """Aggregate stats across all analyses."""
    async with async_session() as session:
        # Total count
        total_r = await session.execute(select(func.count(Analysis.id)))
        total = total_r.scalar() or 0

        if total == 0:
            return {"total_analyses": 0, "risk_distribution": {}, "input_type_distribution": {}, "avg_threat_score": 0}

        # Risk distribution
        dist_r = await session.execute(select(Analysis.verdict, func.count(Analysis.id)).group_by(Analysis.verdict))
        risk_dist = {row[0]: row[1] for row in dist_r.all()}

        # Input type distribution
        all_rows = await session.execute(select(Analysis.input_types))
        type_counts = {}
        for (input_types,) in all_rows.all():
            if input_types:
                for t in input_types:
                    type_counts[t] = type_counts.get(t, 0) + 1

        # Average threat score
        avg_r = await session.execute(select(func.avg(Analysis.threat_score)))
        avg_score = round(avg_r.scalar() or 0, 1)

        # Consistency distribution
        # (computed from breakdown — check if all modalities agree)
        consistency = {"unanimous": 0, "mixed": 0}
        all_analyses = await session.execute(select(Analysis.breakdown))
        for (breakdown,) in all_analyses.all():
            if breakdown:
                labels = set()
                for mod in ["text", "image", "video", "audio"]:
                    if mod in breakdown and isinstance(breakdown[mod], dict):
                        labels.add(breakdown[mod].get("label"))
                if len(labels) <= 1:
                    consistency["unanimous"] += 1
                else:
                    consistency["mixed"] += 1

        return {
            "total_analyses": total,
            "risk_distribution": risk_dist,
            "risk_percentages": {k: round(v / total * 100, 1) for k, v in risk_dist.items()},
            "input_type_distribution": type_counts,
            "avg_threat_score": avg_score,
            "consistency": consistency,
            "consistency_percentages": {k: round(v / total * 100, 1) for k, v in consistency.items()},
        }
