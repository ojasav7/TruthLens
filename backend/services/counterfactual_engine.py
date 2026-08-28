"""Counterfactual Explanation Engine.

Shows which evidence signals have the greatest influence on the assessment.
"These are sensitivity/simulation estimates — never guaranteed outcomes."
"""

import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("truthlens.counterfactual")


@dataclass
class CounterfactualScenario:
    condition: str
    estimated_risk: float
    risk_delta: float
    confidence: str  # "high", "medium", "low" — how confident in this estimate

    def to_dict(self):
        return asdict(self)


@dataclass
class CounterfactualResult:
    current_risk: float
    scenarios: list[dict] = field(default_factory=list)
    disclaimer: str = "These are sensitivity estimates based on model behavior, not guaranteed outcomes."

    def to_dict(self):
        return asdict(self)


def compute_counterfactuals(
    current_risk: float,
    has_provenance: bool = False,
    has_fact_check: bool = False,
    has_audio_video_match: bool = True,
    evidence_strength: float = 0.5,
    model_confidence: float = 0.5,
) -> CounterfactualResult:
    """Estimate risk under hypothetical evidence changes."""
    scenarios = []

    # Scenario: If provenance were verified
    if not has_provenance:
        prov_impact = current_risk * 0.25  # provenance reduces risk by ~25%
        scenarios.append(CounterfactualScenario(
            condition="If provenance were verified",
            estimated_risk=round(max(0, current_risk - prov_impact), 1),
            risk_delta=round(-prov_impact, 1),
            confidence="medium",
        ))

    # Scenario: If fact-check confirmed
    if not has_fact_check:
        fc_impact = current_risk * 0.20
        scenarios.append(CounterfactualScenario(
            condition="If fact-check result confirmed the claim",
            estimated_risk=round(max(0, current_risk - fc_impact), 1),
            risk_delta=round(-fc_impact, 1),
            confidence="medium",
        ))

    # Scenario: If audio/video temporal mismatch resolved
    if not has_audio_video_match:
        av_impact = current_risk * 0.15
        scenarios.append(CounterfactualScenario(
            condition="If audio/video temporal mismatch were resolved",
            estimated_risk=round(max(0, current_risk - av_impact), 1),
            risk_delta=round(-av_impact, 1),
            confidence="low",
        ))

    # Scenario: If evidence strength doubled
    if evidence_strength < 0.5:
        ev_impact = current_risk * 0.18
        scenarios.append(CounterfactualScenario(
            condition="If evidence strength were significantly stronger",
            estimated_risk=round(max(0, current_risk - ev_impact), 1),
            risk_delta=round(-ev_impact, 1),
            confidence="low",
        ))

    # Scenario: If models agreed
    if model_confidence < 0.6:
        mc_impact = current_risk * 0.12
        scenarios.append(CounterfactualScenario(
            condition="If model confidence were higher",
            estimated_risk=round(max(0, current_risk - mc_impact), 1),
            risk_delta=round(-mc_impact, 1),
            confidence="low",
        ))

    # Combined scenario
    if len(scenarios) >= 2:
        combined_delta = sum(s.risk_delta for s in scenarios)
        scenarios.append(CounterfactualScenario(
            condition="If ALL above conditions were resolved",
            estimated_risk=round(max(0, current_risk + combined_delta), 1),
            risk_delta=round(combined_delta, 1),
            confidence="low",
        ))

    return CounterfactualResult(
        current_risk=current_risk,
        scenarios=[s.to_dict() for s in scenarios],
    )
