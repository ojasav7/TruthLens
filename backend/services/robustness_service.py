"""Robustness Lab — applies controlled transformations and measures prediction delta."""

import io
from PIL import Image, ImageFilter
import numpy as np


def transform_image(img: Image.Image, operation: str, **kwargs) -> Image.Image:
    """Apply a transformation to an image. Always returns a new copy."""
    if operation == "compress":
        quality = kwargs.get("quality", 30)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    elif operation == "resize":
        factor = kwargs.get("factor", 0.5)
        w, h = img.size
        return img.resize((int(w * factor), int(h * factor)), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    elif operation == "brightness":
        factor = kwargs.get("factor", 1.5)
        return Image.fromarray(np.clip(np.array(img) * factor, 0, 255).astype(np.uint8))
    elif operation == "noise":
        arr = np.array(img).astype(np.int16)
        noise = np.random.randint(-30, 30, arr.shape, dtype=np.int16)
        return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    elif operation == "blur":
        return img.filter(ImageFilter.GaussianBlur(radius=kwargs.get("radius", 3)))
    return img


async def run_robustness_test(file_bytes: bytes, filename: str, content_type: str, modality: str = "image") -> dict:
    """Run image through multiple transformations and compare predictions."""
    from backend.services.model_loader import get_image_model
    from PIL import Image

    if modality != "image":
        return {"error": "Currently only image robustness testing is supported"}

    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    model = get_image_model()

    transformations = {
        "original": img,
        "compress_q30": transform_image(img, "compress", quality=30),
        "compress_q50": transform_image(img, "compress", quality=50),
        "compress_q90": transform_image(img, "compress", quality=90),
        "resize_50": transform_image(img, "resize", factor=0.5),
        "resize_25": transform_image(img, "resize", factor=0.25),
        "brighten": transform_image(img, "brightness", factor=1.5),
        "noise": transform_image(img, "noise"),
        "blur": transform_image(img, "blur", radius=3),
    }

    results = {}
    for name, transformed in transformations.items():
        try:
            pred = model.predict(transformed)
            results[name] = {"label": pred["label"], "confidence": round(pred["confidence"], 4)}
        except Exception as e:
            results[name] = {"error": str(e)}

    # Calculate robustness score: how stable are predictions across transforms
    labels = [r.get("label") for r in results.values() if "label" in r]
    original_label = labels[0] if labels else None
    agreement = sum(1 for l in labels if l == original_label) / len(labels) if labels else 0

    return {
        "original_label": original_label,
        "transformations": results,
        "robustness_score": round(agreement * 100, 1),
        "total_transforms": len(transformations),
        "label_stable": agreement >= 0.8,
    }
