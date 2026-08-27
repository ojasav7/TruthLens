"""Image Forensics — Error Level Analysis (ELA) and tampering detection.

ELA works by re-saving a JPEG at a known quality level, then computing
the difference between original and re-saved. Edited/spliced regions
show higher error levels because they were saved at a different quality
than the rest of the image.
"""

import io
import hashlib
from PIL import Image, ImageChops, ImageStat
import numpy as np


def error_level_analysis(image_bytes: bytes, quality: int = 90) -> dict:
    """
    Perform Error Level Analysis on an image.

    Returns:
        {
            "ela_score": float (0-100, higher = more tampering),
            "suspicious_regions": int,
            "mean_error": float,
            "max_error": float,
            "histogram": dict,
            "explanation": str,
        }
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return {"error": f"Cannot open image: {e}"}

    # Re-save at known quality
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    resaved = Image.open(buf).convert("RGB")

    # Compute difference
    diff = ImageChops.difference(img, resaved)
    stat = ImageStat.Stat(diff)

    # Mean and max error across channels
    mean_error = sum(stat.mean) / len(stat.mean)
    max_error = max(stat.extrema[0][1], stat.extrema[1][1], stat.extrema[2][1])

    # Convert to numpy for histogram analysis
    diff_arr = np.array(diff)
    gray_diff = np.mean(diff_arr, axis=2)  # average across RGB

    # Histogram of error levels
    hist, bin_edges = np.histogram(gray_diff, bins=10, range=(0, 255))
    histogram = {f"{int(bin_edges[i])}-{int(bin_edges[i+1])}": int(hist[i]) for i in range(len(hist))}

    # Suspicious regions: pixels with error > 2x mean
    threshold = mean_error * 2.5 if mean_error > 0 else 30
    suspicious_mask = gray_diff > threshold
    suspicious_pixels = int(np.sum(suspicious_mask))
    total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
    suspicious_ratio = suspicious_pixels / total_pixels if total_pixels > 0 else 0

    # ELA score: 0 = clean, 100 = heavily tampered
    ela_score = min(100, suspicious_ratio * 500 + mean_error * 0.5)

    # Explanation
    if ela_score > 70:
        explanation = "High tampering indicators — likely manipulated or spliced"
    elif ela_score > 40:
        explanation = "Moderate tampering indicators — possible editing detected"
    elif ela_score > 15:
        explanation = "Low tampering indicators — some compression artifacts"
    else:
        explanation = "No significant tampering detected"

    return {
        "ela_score": round(float(ela_score), 2),
        "suspicious_regions": int(suspicious_pixels),
        "suspicious_ratio": round(float(suspicious_ratio), 4),
        "mean_error": round(float(mean_error), 4),
        "max_error": int(max_error),
        "histogram": histogram,
        "explanation": explanation,
    }


def detect_copy_move(image_bytes: bytes) -> dict:
    """
    Simple copy-move detection via block matching.
    Checks if any large region of the image is a near-duplicate of another.

    Returns:
        {
            "suspected_copy_move": bool,
            "confidence": float,
            "explanation": str,
        }
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale
    except Exception as e:
        return {"error": f"Cannot open image: {e}"}

    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape

    if h < 64 or w < 64:
        return {
            "suspected_copy_move": False,
            "confidence": 0.0,
            "explanation": "Image too small for copy-move analysis",
        }

    # Divide into blocks and compute hashes
    block_size = 16
    step = 8
    blocks = {}

    for y in range(0, h - block_size, step):
        for x in range(0, w - block_size, step):
            block = arr[y:y+block_size, x:x+block_size]
            # Simple perceptual hash: mean + std of block
            block_hash = (round(float(np.mean(block)), 1), round(float(np.std(block)), 1))
            key = block_hash
            if key not in blocks:
                blocks[key] = []
            blocks[key].append((x, y))

    # Find blocks with many duplicates at different positions
    max_duplicates = 0
    for key, positions in blocks.items():
        if len(positions) > 3:
            # Check that positions are far apart (not adjacent blocks)
            coords = np.array(positions)
            if len(coords) > 1:
                from scipy.spatial.distance import pdist
                distances = pdist(coords)
                far_pairs = np.sum(distances > block_size * 4)
                if far_pairs > max_duplicates:
                    max_duplicates = far_pairs

    confidence = float(min(1.0, max_duplicates / 20))
    suspected = bool(confidence > 0.3)

    explanation = (
        "Possible copy-move forgery detected" if suspected
        else "No copy-move patterns detected"
    )

    return {
        "suspected_copy_move": suspected,
        "confidence": round(confidence, 4),
        "duplicated_blocks": int(max_duplicates),
        "explanation": explanation,
    }


def full_forensics(image_bytes: bytes) -> dict:
    """Run all image forensics checks."""
    ela = error_level_analysis(image_bytes)
    copy_move = detect_copy_move(image_bytes)

    # Overall tampering score
    ela_score = ela.get("ela_score", 0)
    copy_score = copy_move.get("confidence", 0) * 100
    overall = round(max(ela_score, copy_score, (ela_score + copy_score) / 2), 2)

    if overall > 60:
        verdict = "LIKELY_TAMPERED"
    elif overall > 30:
        verdict = "POSSIBLY_TAMPERED"
    else:
        verdict = "LIKELY_AUTHENTIC"

    return {
        "ela": ela,
        "copy_move": copy_move,
        "overall_score": float(overall),
        "verdict": verdict,
        "sha256": hashlib.sha256(image_bytes).hexdigest(),
    }
