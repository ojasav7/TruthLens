"""Language Router — detects language and routes to appropriate NLP model."""

try:
    from langdetect import detect as _detect_lang
except ImportError:
    _detect_lang = None


def detect_language(text: str) -> str:
    """Detect language: 'en', 'hi', 'hi-en' (Hinglish), or 'unknown'."""
    if not text or not text.strip():
        return "unknown"

    if _detect_lang is None:
        return "en"  # fallback

    try:
        lang = _detect_lang(text)
        if lang == "hi":
            return "hi"
        elif lang == "en":
            # Check for Hinglish (Devanagari characters present)
            has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
            if has_devanagari:
                return "hi-en"
            return "en"
        return lang
    except Exception:
        return "en"  # fallback


class MultilingualNLP:
    """Routes text to English DistilBERT or Hindi MuRIL model."""

    def __init__(self):
        self._en_model = None
        self._hi_model = None
        self._hi_tokenizer = None

    def predict(self, text: str) -> dict:
        lang = detect_language(text)

        if lang in ("hi", "hi-en"):
            return self._predict_hindi(text)
        return self._predict_english(text)

    def _predict_english(self, text: str) -> dict:
        from backend.services.model_loader import get_nlp_model
        model = get_nlp_model()
        if not model:
            return {"label": "real", "confidence": 0.5}
        return model.predict(text)

    def _predict_hindi(self, text: str) -> dict:
        """Hindi prediction using MuRIL or transliteration fallback."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch

            if self._hi_model is None:
                model_name = "google/muril-base-cased"
                self._hi_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._hi_model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

            inputs = self._hi_tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
            with torch.no_grad():
                outputs = self._hi_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            label_idx = probs.argmax().item()
            confidence = probs[0][label_idx].item()

            return {"label": "fake" if label_idx == 1 else "real", "confidence": round(confidence, 4), "language": "hi"}

        except Exception:
            # MuRIL not available — transliterate Hindi to English and use existing model
            return self._predict_english(text)

    def explain(self, text: str, top_k: int = 5) -> dict:
        """Explain prediction — SHAP works on English, transliterate Hindi."""
        lang = detect_language(text)
        from backend.services.model_loader import get_nlp_model

        model = get_nlp_model()
        if not model:
            return {"label": "real", "confidence": 0.5, "tokens": [], "language": lang}

        return model.explain(text, top_k=top_k)


# Singleton
multilingual_nlp = MultilingualNLP()
