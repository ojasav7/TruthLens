"""AI-Generated Text Detection — detects ChatGPT/Claude/Gemini written text.

Uses two signals:
- Perplexity: how "surprised" a language model is by the text.
  AI text has abnormally LOW perplexity (too predictable).
- Burstiness: variation in sentence complexity.
  AI text has abnormally LOW burstiness (too uniform).

No external API needed — uses the NLP model's own tokenizer for perplexity
and stdlib statistics for burstiness.
"""

import math
import re
import statistics
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\b\w+\b|[^\w\s]", text.lower())


def _sentence_split(text: str) -> list[str]:
    """Split text into sentences."""
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if len(s.strip()) > 3]


def _word_entropy(tokens: list[str]) -> float:
    """Shannon entropy of the token distribution.
    AI text tends to have higher entropy (more uniform word usage).
    """
    if not tokens:
        return 0.0
    freq = Counter(tokens)
    total = len(tokens)
    entropy = -sum((c / total) * math.log2(c / total) for c in freq.values())
    return entropy


def _sentence_length_variance(sentences: list[str]) -> float:
    """Variance in sentence lengths.
    Human writing varies a lot; AI writing is more uniform.
    """
    if len(sentences) < 2:
        return 0.0
    lengths = [len(s.split()) for s in sentences]
    return statistics.variance(lengths)


def _repetition_score(tokens: list[str], n: int = 3) -> float:
    """Fraction of n-grams that repeat. AI text repeats phrases more."""
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
    freq = Counter(ngrams)
    repeated = sum(c - 1 for c in freq.values() if c > 1)
    return repeated / len(ngrams)


def detect_ai_text(text: str) -> dict:
    """
    Analyze text for signs of AI generation.

    Returns:
        {
            "is_ai_generated": bool,
            "confidence": float (0-1, higher = more likely AI),
            "signals": {
                "perplexity_score": float (0-1, lower = more AI-like),
                "burstiness": float (0-1, lower = more AI-like),
                "entropy": float,
                "repetition": float,
                "avg_sentence_length": float,
                "sentence_length_variance": float,
            },
            "explanation": str,
        }
    """
    if not text or not text.strip():
        return {
            "is_ai_generated": False,
            "confidence": 0.0,
            "signals": {},
            "explanation": "Empty text",
        }

    tokens = _tokenize(text)
    sentences = _sentence_split(text)

    # --- Perplexity proxy: normalized inverse entropy ---
    # Low entropy = high predictability = more AI-like
    entropy = _word_entropy(tokens)
    # Typical human text entropy: 3.5-5.0 bits/token
    # AI text entropy: often 2.5-4.0 bits/token
    perplexity_score = max(0, min(1, 1.0 - (entropy - 2.0) / 3.0))

    # --- Burstiness: sentence length variance ---
    sl_var = _sentence_length_variance(sentences)
    avg_sl = statistics.mean([len(s.split()) for s in sentences]) if sentences else 0
    # Human burstiness: high variance (300-1000+)
    # AI burstiness: low variance (50-200)
    burstiness = max(0, min(1, 1.0 - sl_var / 500))

    # --- Repetition ---
    repetition = _repetition_score(tokens, n=3)

    # --- Combine signals ---
    # Weighted average: perplexity (40%), burstiness (35%), repetition (25%)
    confidence = (
        0.40 * perplexity_score +
        0.35 * burstiness +
        0.25 * min(1.0, repetition * 5)  # scale repetition
    )
    confidence = round(min(1.0, max(0.0, confidence)), 4)

    is_ai = confidence >= 0.6

    # --- Explanation ---
    reasons = []
    if perplexity_score > 0.6:
        reasons.append("Text is unusually predictable (low perplexity)")
    if burstiness > 0.6:
        reasons.append("Sentence structure is too uniform (low burstiness)")
    if repetition > 0.05:
        reasons.append(f"Phrase repetition detected ({repetition:.1%})")
    if avg_sl > 0:
        reasons.append(f"Average sentence length: {avg_sl:.0f} words")

    explanation = "Likely AI-generated" if is_ai else "Likely human-written"
    if reasons:
        explanation += ". " + "; ".join(reasons)

    return {
        "is_ai_generated": is_ai,
        "confidence": confidence,
        "signals": {
            "perplexity_score": round(perplexity_score, 4),
            "burstiness": round(burstiness, 4),
            "entropy": round(entropy, 4),
            "repetition": round(repetition, 4),
            "avg_sentence_length": round(avg_sl, 1),
            "sentence_length_variance": round(sl_var, 2),
        },
        "explanation": explanation,
    }
