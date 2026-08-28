"""Investigation Copilot.

Evidence-grounded Q&A from investigation context. Not a chatbot.
If insufficient info: "The available investigation evidence does not establish this."
"""

import logging

logger = logging.getLogger("truthlens.copilot")


# ponytail: handler dict replaces 237-line if/elif. Add more keys to add more questions.
_HANDLERS = {}


def _register(*keywords):
    def deco(fn):
        for kw in keywords:
            _HANDLERS[kw] = fn
        return fn
    return deco


def _answer(evidence, **_kw):
    supporting = [e for e in evidence if e.get("category") in ("POSITIVE", "SUPPORTS") or e.get("score", 0) > 0.5]
    if not supporting:
        return {"answer": "No clear supporting signals found.", "citations": [], "confidence": "LOW"}
    return {"answer": f"{len(supporting)} evidence item(s) support the assessment.", "citations": [{"id": e.get("id")} for e in supporting[:5]], "confidence": "MEDIUM"}


@_register("contradict", "conflict")
def _contradicting(evidence, conflicts=None, **_kw):
    contradicting = [e for e in evidence if e.get("category") in ("NEGATIVE", "CONTRADICTS")]
    n_conflicts = (conflicts or {}).get("total_conflicts", 0)
    if not contradicting and n_conflicts == 0:
        return {"answer": "No contradicting evidence identified.", "citations": [], "confidence": "HIGH"}
    return {"answer": f"{len(contradicting)} contradicting item(s), {n_conflicts} conflict(s).", "citations": [{"id": e.get("id")} for e in contradicting[:5]], "confidence": "MEDIUM"}


@_register("strongest")
def _strongest(evidence, **_kw):
    if not evidence:
        return {"answer": "No evidence available.", "citations": [], "confidence": "N/A"}
    best = max(evidence, key=lambda e: abs(e.get("score", 0)))
    return {"answer": f"Strongest: {best.get('description', 'N/A')[:80]} (score: {best.get('score', 0):.2f})", "citations": [{"id": best.get("id")}], "confidence": "HIGH"}


@_register("weakest")
def _weakest(evidence, **_kw):
    if not evidence:
        return {"answer": "No evidence available.", "citations": [], "confidence": "N/A"}
    worst = min(evidence, key=lambda e: abs(e.get("score", 0.5)))
    return {"answer": f"Weakest: {worst.get('description', 'N/A')[:80]} (score: {worst.get('score', 0):.2f})", "citations": [{"id": worst.get("id")}], "confidence": "MEDIUM"}


@_register("missing", "what information")
def _missing(evidence, analyses=None, **_kw):
    cats = {e.get("type") for e in evidence}
    missing = []
    if "provenance" not in cats: missing.append("Provenance data")
    if "source" not in cats: missing.append("Independent source verification")
    if len(analyses or []) < 2: missing.append("Cross-modal analysis")
    if not missing:
        return {"answer": "Key evidence categories appear covered.", "citations": [], "confidence": "MEDIUM"}
    return {"answer": f"Missing: {', '.join(missing)}.", "citations": [], "confidence": "MEDIUM", "recommended_next": f"Verify {missing[0].lower()}"}


@_register("uncertain", "why not certain")
def _uncertain(uncertainty=None, **_kw):
    reasons = (uncertainty or {}).get("sources", [])
    if not reasons:
        return {"answer": "No major uncertainty sources identified.", "citations": [], "confidence": "HIGH"}
    return {"answer": f"Uncertainty is {(uncertainty or {}).get('level', '?')} because: {'; '.join(reasons[:3])}.", "citations": [], "confidence": "MEDIUM"}


@_register("verify", "next", "next step")
def _next_steps(evidence, **_kw):
    cats = {e.get("type") for e in evidence}
    suggestions = []
    if "provenance" not in cats: suggestions.append("Verify provenance")
    if "source" not in cats: suggestions.append("Identify independent sources")
    if "fact_check" not in cats: suggestions.append("Complete fact-check")
    if not suggestions: suggestions.append("Review existing evidence")
    return {"answer": f"Next steps: {'; '.join(suggestions)}.", "citations": [], "confidence": "MEDIUM"}


@_register("change", "would change")
def _what_changes(evidence, **_kw):
    return {"answer": "Assessment most sensitive to: provenance, independent sources, cross-modal consistency.", "citations": [{"id": e.get("id")} for e in evidence[:3]], "confidence": "MEDIUM"}


@_register("reproduc")
def _reproducible(analyses=None, **_kw):
    if len(analyses or []) < 2:
        return {"answer": "Reproduction requires at least two analyses of the same content.", "citations": [], "confidence": "N/A"}
    return {"answer": "Compare analysis signals across runs for reproducibility.", "citations": [], "confidence": "MEDIUM"}


@_register("disagree")
def _disagreement(model_signals=None, **_kw):
    if not model_signals or len(model_signals) < 2:
        return {"answer": "Insufficient model signals.", "citations": [], "confidence": "N/A"}
    labels = [s.get("label") for s in model_signals]
    if len(set(labels)) > 1:
        disagree_str = ", ".join(s.get("modality", "?") + ": " + s.get("label", "?") for s in model_signals)
        return {"answer": f"Models disagree: {disagree_str}.", "citations": [], "confidence": "HIGH"}
    return {"answer": "All model signals agree.", "citations": [], "confidence": "HIGH"}


@_register("corroborate")
def _corroboration(evidence, **_kw):
    sources = {}
    for e in evidence:
        sources.setdefault(e.get("source_module", "?"), []).append(e)
    multi = {s: items for s, items in sources.items() if len(items) >= 2}
    if not multi:
        return {"answer": "No source corroboration detected.", "citations": [], "confidence": "MEDIUM"}
    return {"answer": f"Corroborating: {', '.join(multi.keys())}.", "citations": [], "confidence": "MEDIUM"}


@_register("independent")
def _independence(evidence, **_kw):
    sources = {}
    for e in evidence:
        sources.setdefault(e.get("source_module", "?"), []).append(e)
    independent = [s for s, items in sources.items() if len(items) <= 2]
    return {"answer": f"{len(independent)} source(s) appear independent: {', '.join(independent) if independent else 'none confirmed'}.", "citations": [], "confidence": "LOW"}


def answer_question(question: str, evidence: list | None = None, **kwargs) -> dict:
    """Answer grounded in available investigation data."""
    evidence = evidence or []
    q = question.lower().strip()

    # Find matching handler
    for keyword, handler in _HANDLERS.items():
        if keyword in q:
            return handler(evidence=evidence, **kwargs)

    return {
        "answer": "I can answer about evidence support, contradictions, missing info, uncertainty, and next steps.",
        "citations": [],
        "confidence": "N/A",
    }
