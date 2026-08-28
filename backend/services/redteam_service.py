"""Red Team / Robustness Testing Mode.

Dedicated testing environment that attempts to identify conditions
under which detection becomes less reliable. Isolated from production.
"""

import io
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger("truthlens.redteam")


@dataclass
class TransformResult:
    name: str
    score: float
    diff: float
    description: str

    def to_dict(self):
        return asdict(self)


@dataclass
class RobustnessReport:
    modality: str
    original_score: float
    transformations: list[dict] = field(default_factory=list)
    robustness_score: float = 0.0
    worst_degradation: float = 0.0
    worst_transform: str = ""
    model_version: str = "unknown"

    def to_dict(self):
        return asdict(self)


# --- Image transforms ---
def _resize(img: Image.Image, factor: float = 0.5) -> Image.Image:
    w, h = img.size
    return img.resize((int(w * factor), int(h * factor)), Image.Resampling.LANCZOS)


def _crop(img: Image.Image, pct: float = 0.2) -> Image.Image:
    w, h = img.size
    margin = int(min(w, h) * pct)
    return img.crop((margin, margin, w - margin, h - margin))


def _brightness(img: Image.Image, factor: float = 1.5) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(factor)


def _contrast(img: Image.Image, factor: float = 1.5) -> Image.Image:
    return ImageEnhance.Contrast(img).enhance(factor)


def _noise(img: Image.Image, severity: int = 30) -> Image.Image:
    arr = np.array(img).astype(np.int16)
    noise = np.random.randint(-severity, severity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _blur(img: Image.Image, radius: int = 3) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def _jpeg_recompress(img: Image.Image, quality: int = 30) -> Image.Image:
    buf = io.BytesIO()
    rgb = img.convert("RGB")
    rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert(img.mode)


IMAGE_TRANSFORMS = {
    "resize_50": lambda img: _resize(img, 0.5),
    "resize_25": lambda img: _resize(img, 0.25),
    "crop_20": lambda img: _crop(img, 0.2),
    "brightness_high": lambda img: _brightness(img, 1.5),
    "brightness_low": lambda img: _brightness(img, 0.6),
    "contrast_high": lambda img: _contrast(img, 1.5),
    "noise_30": lambda img: _noise(img, 30),
    "noise_50": lambda img: _noise(img, 50),
    "blur_3": lambda img: _blur(img, 3),
    "jpeg_recompress_30": lambda img: _jpeg_recompress(img, 30),
}


def run_robustness_test(
    image_bytes: bytes,
    predict_fn,
    model_version: str = "unknown",
) -> dict:
    """Run all image transformations and report robustness."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return RobustnessReport(
            modality="image",
            original_score=0.0,
            robustness_score=0.0,
            model_version=model_version,
            transformations=[{"error": str(e)}],
        ).to_dict()

    # Get original prediction
    original_result = predict_fn(image_bytes)
    original_score = original_result.get("confidence", 0.0)
    if original_result.get("label") == "real":
        original_score = 1.0 - original_score

    results = []
    for name, transform_fn in IMAGE_TRANSFORMS.items():
        try:
            transformed = transform_fn(img)
            buf = io.BytesIO()
            transformed.save(buf, format="PNG")
            transformed_bytes = buf.getvalue()

            result = predict_fn(transformed_bytes)
            t_score = result.get("confidence", 0.0)
            if result.get("label") == "real":
                t_score = 1.0 - t_score

            diff = abs(original_score - t_score)
            results.append(TransformResult(
                name=name,
                score=round(t_score, 4),
                diff=round(diff, 4),
                description=f"Score changed by {diff:.1%}",
            ).to_dict())
        except Exception as e:
            results.append({"name": name, "error": str(e)})

    # Compute robustness score (lower degradation = more robust)
    diffs = [r["diff"] for r in results if "diff" in r]
    avg_degradation = sum(diffs) / len(diffs) if diffs else 0.0
    worst = max(diffs) if diffs else 0.0
    worst_name = next((r["name"] for r in results if r.get("diff") == worst), "none")

    robustness = max(0, round((1 - avg_degradation) * 100, 1))

    return RobustnessReport(
        modality="image",
        original_score=round(original_score, 4),
        transformations=results,
        robustness_score=robustness,
        worst_degradation=round(worst, 4),
        worst_transform=worst_name,
        model_version=model_version,
    ).to_dict()
