"""
NLP Fake News Classifier — Phase 1
Uses fine-tuned DistilBERT for binary fake/real classification.
DistilBERT is 40% smaller and 60% faster than BERT with ~97% performance.
"""

import os
from pathlib import Path

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "nlp" / "weights"


class FakeNewsClassifier:
    """Binary fake news classifier built on DistilBERT."""

    def __init__(self, weights_path: str | Path | None = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR

        if (self.path / "config.json").exists():
            self.tokenizer = DistilBertTokenizer.from_pretrained(str(self.path))
            self.model = DistilBertForSequenceClassification.from_pretrained(str(self.path))
        else:
            # Fallback: use base model (for skeleton/testing before training)
            print(f"No weights found at {self.path}, using untrained distilbert-base-uncased")
            self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
            self.model = DistilBertForSequenceClassification.from_pretrained(
                "distilbert-base-uncased", num_labels=2
            )

        self.model.to(self.device)
        self.model.eval()
        self.labels = ["real", "fake"]

    def predict(self, text: str) -> dict:
        """
        Classify a text as fake or real.

        Args:
            text: The input text to classify.

        Returns:
            {"label": "fake"|"real", "confidence": float}
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            pred_idx = probs.argmax(dim=-1).item()
            confidence = probs[0][pred_idx].item()

        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
        }

    def explain(self, text: str, top_k: int = 10) -> dict:
        """
        Predict with SHAP token-level explanation.

        Returns prediction + token attributions showing which words
        drove the classification.
        """
        import shap

        def model_fn(texts):
            """Batched callable: strings in, (n, 2) logits out."""
            enc = self.tokenizer(
                list(texts),
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            ).to(self.device)
            with torch.inference_mode():
                logits = self.model(**enc).logits
            return logits.detach().cpu().numpy()

        # SHAP skill: use Text masker + PartitionExplainer
        masker = shap.maskers.Text(self.tokenizer)
        explainer = shap.Explainer(
            model_fn,
            masker,
            algorithm="partition",
            output_names=["real", "fake"],
        )

        # Explain logit output (additive evidence per the SHAP skill)
        explanation = explainer([text], max_evals=300)

        # Select the predicted class output
        pred = self.predict(text)
        class_idx = 1 if pred["label"] == "fake" else 0
        class_exp = explanation[..., class_idx]

        # Extract token attributions as a list of (token, value) pairs
        tokens = class_exp.data[0] if class_exp.data is not None else []
        values = class_exp.values[0]

        # Sort by absolute attribution magnitude, take top_k
        pairs = list(zip(tokens, values))
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        top_tokens = [
            {"token": t, "attribution": round(float(v), 4)}
            for t, v in pairs[:top_k]
        ]

        return {
            "label": pred["label"],
            "confidence": pred["confidence"],
            "explained_output": "logits",
            "class_index": class_idx,
            "class_name": pred["label"],
            "tokens": top_tokens,
            "base_value": round(float(class_exp.base_values[0]), 4),
        }
