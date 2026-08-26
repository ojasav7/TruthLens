"""Multimodal Contradiction Engine — consumes model outputs, detects cross-modal disagreements."""


class ContradictionEngine:
    def analyze(self, breakdown: dict) -> dict:
        """Detect whether modalities agree or contradict each other."""
        labels = {}
        for modality in ["text", "image", "video", "audio"]:
            result = breakdown.get(modality)
            if result and isinstance(result, dict) and "label" in result:
                labels[modality] = result["label"]

        if len(labels) < 2:
            return {"status": "insufficient_data", "score": 0.0, "signals": []}

        unique_labels = set(labels.values())
        if len(unique_labels) == 1:
            agreement = 1.0
            status = "consistent"
        else:
            # How much do they disagree (0=perfect agreement, 1=total split)
            agreement = 1.0 - (len(unique_labels) - 1) / len(unique_labels)
            status = "inconsistent"

        signals = []
        modalities = list(labels.keys())
        for i in range(len(modalities)):
            for j in range(i + 1, len(modalities)):
                m1, m2 = modalities[i], modalities[j]
                if labels[m1] != labels[m2]:
                    signals.append({
                        "type": f"{m1}_{m2}_mismatch",
                        "description": f"{m1} says '{labels[m1]}' but {m2} says '{labels[m2]}'",
                        "confidence": abs(
                            breakdown[m1].get("confidence", 0.5) - breakdown[m2].get("confidence", 0.5)
                        ),
                    })

        return {"status": status, "score": round(1.0 - agreement, 2), "signals": signals}
