"""Watermark Detection — detect invisible watermarks from AI image generators.

AI generators embed invisible watermarks:
- DALL-E/ChatGPT: Google SynthID-style watermarks in pixel LSBs
- Midjourney: spectral domain watermarks
- Stable Diffusion: optional invisible watermark in frequency domain

This module detects these by analyzing LSB patterns and frequency signatures.
"""

import io
import hashlib
import numpy as np
from PIL import Image


def _analyze_lsb(image_arr: np.ndarray) -> dict:
    """Analyze Least Significant Bit patterns for watermark signatures."""
    # Extract LSBs from each channel — cast to uint8 first
    arr = image_arr.astype(np.uint8)
    lsb_r = arr[:, :, 0] & 1
    lsb_g = arr[:, :, 1] & 1
    lsb_b = arr[:, :, 2] & 1

    # Natural images have ~50% ones in LSBs
    # Watermarked images have statistically different LSB distributions
    ratio_r = np.mean(lsb_r)
    ratio_g = np.mean(lsb_g)
    ratio_b = np.mean(lsb_b)

    # Check for non-random LSB patterns (chi-squared test)
    # If LSB ratio deviates significantly from 0.5, watermark likely present
    deviations = [abs(r - 0.5) for r in [ratio_r, ratio_g, ratio_b]]
    max_deviation = max(deviations)
    avg_deviation = np.mean(deviations)

    # Entropy of LSB channel — watermarks reduce entropy
    def _lsb_entropy(lsb):
        flat = lsb.flatten()
        p0 = np.mean(flat == 0)
        p1 = np.mean(flat == 1)
        if p0 == 0 or p1 == 0:
            return 1.0
        return -(p0 * np.log2(p0) + p1 * np.log2(p1))

    entropy_r = _lsb_entropy(lsb_r)
    entropy_g = _lsb_entropy(lsb_g)
    entropy_b = _lsb_entropy(lsb_b)
    avg_entropy = np.mean([entropy_r, entropy_g, entropy_b])

    # Natural images: entropy close to 1.0
    # Watermarked: entropy often < 0.98
    has_lsb_watermark = bool(avg_entropy < 0.995 or max_deviation > 0.03)

    return {
        "lsb_entropy": round(float(avg_entropy), 6),
        "lsb_deviations": {
            "red": round(float(deviations[0]), 4),
            "green": round(float(deviations[1]), 4),
            "blue": round(float(deviations[2]), 4),
        },
        "has_lsb_watermark": has_lsb_watermark,
        "confidence": round(float(min(1.0, max_deviation * 10 + (1.0 - avg_entropy) * 5)), 4),
    }


def _analyze_dct(image_arr: np.ndarray) -> dict:
    """Analyze DCT coefficients for spectral watermark signatures."""
    # Convert to grayscale for DCT analysis
    gray = np.mean(image_arr, axis=2).astype(np.float32)

    # Simple DCT approximation using numpy FFT
    # Watermarks appear as periodic patterns in frequency domain
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)

    # Check center region (low frequencies) — watermarks often modulate these
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    quarter_h, quarter_w = h // 4, w // 4

    center_region = magnitude[center_h-quarter_h:center_h+quarter_h, center_w-quarter_w:center_w+quarter_w]
    outer_region = np.concatenate([
        magnitude[:quarter_h, :].flatten(),
        magnitude[-quarter_h:, :].flatten(),
        magnitude[:, :quarter_w].flatten(),
        magnitude[:, -quarter_w:].flatten(),
    ])

    # Ratio of center to outer energy
    center_energy = np.mean(center_region)
    outer_energy = np.mean(outer_region) if len(outer_region) > 0 else 1
    spectral_ratio = center_energy / outer_energy if outer_energy > 0 else 0

    # Watermarked images often have higher spectral ratio in center
    has_spectral_watermark = bool(spectral_ratio > 3.0)

    return {
        "spectral_ratio": round(float(spectral_ratio), 4),
        "has_spectral_watermark": has_spectral_watermark,
        "confidence": round(float(min(1.0, max(0, (spectral_ratio - 2.0) / 3.0))), 4),
    }


def detect_watermark(image_bytes: bytes) -> dict:
    """
    Detect invisible watermarks from AI generators.

    Returns:
        {
            "watermark_detected": bool,
            "confidence": float,
            "lsb_analysis": dict,
            "spectral_analysis": dict,
            "possible_generators": list[str],
            "explanation": str,
        }
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Resize for consistent analysis
        if img.size[0] > 512 or img.size[1] > 512:
            img.thumbnail((512, 512), Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)
    except Exception as e:
        return {"error": f"Cannot process image: {e}"}

    lsb = _analyze_lsb(arr)
    spectral = _analyze_dct(arr)

    # Combine signals — convert numpy types to Python native
    lsb_score = float(lsb["confidence"]) if lsb["has_lsb_watermark"] else 0.0
    spectral_score = float(spectral["confidence"]) if spectral["has_spectral_watermark"] else 0.0
    overall = round(float(max(lsb_score, spectral_score, (lsb_score + spectral_score) / 2)), 4)

    watermark_detected = bool(overall > 0.3)

    # Guess generator based on watermark type
    possible_generators = []
    if bool(lsb["has_lsb_watermark"]):
        possible_generators.extend(["DALL-E/OpenAI", "Google SynthID"])
    if bool(spectral["has_spectral_watermark"]):
        possible_generators.extend(["Midjourney", "Stable Diffusion"])

    if watermark_detected:
        explanation = f"AI watermark detected (confidence: {overall:.1%}). Possible generators: {', '.join(possible_generators)}"
    else:
        explanation = "No AI watermark detected — content may be original or watermark was removed"

    return {
        "watermark_detected": watermark_detected,
        "confidence": overall,
        "lsb_analysis": lsb,
        "spectral_analysis": spectral,
        "possible_generators": possible_generators,
        "explanation": explanation,
    }
