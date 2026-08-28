"""Near-Duplicate Media Detection.

Detects media that is effectively the same even when resized, compressed,
cropped, or slightly modified. Uses perceptual fingerprinting beyond SHA-256.
"""

import logging
import hashlib
import struct
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np

logger = logging.getLogger("truthlens.similarity")


@dataclass
class SimilarityResult:
    is_near_duplicate: bool
    similarity_score: float  # 0-100
    match_analysis_id: str | None = None
    match_media_id: str | None = None
    previous_risk: float | None = None
    previous_verdict: str | None = None
    fingerprint_type: str = "perceptual"

    def to_dict(self):
        return asdict(self)


def compute_perceptual_hash(image_bytes: bytes, hash_size: int = 16) -> str | None:
    """Compute a perceptual hash (pHash) for an image — resistant to resize/compress."""
    try:
        import io
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = np.array(img, dtype=float)
        # DCT-like: compare adjacent pixels
        diff = pixels[:, 1:] > pixels[:, :-1]
        return "".join("1" if b else "0" for b in diff.flatten())
    except Exception as e:
        logger.warning("Perceptual hash failed: %s", e)
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """Hamming distance between two binary strings."""
    if len(hash1) != len(hash2):
        return max(len(hash1), len(hash2))
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def compute_similarity(hash1: str, hash2: str) -> float:
    """Similarity score 0-100 from two perceptual hashes."""
    dist = hamming_distance(hash1, hash2)
    max_dist = len(hash1)
    return round((1 - dist / max_dist) * 100, 1) if max_dist > 0 else 0.0


def compare_media(
    source_bytes: bytes,
    candidate_bytes: bytes,
    source_content_type: str = "",
) -> dict:
    """Compare two media files for near-duplicate detection."""
    # Exact match first
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    if source_sha == candidate_sha:
        return SimilarityResult(
            is_near_duplicate=True,
            similarity_score=100.0,
            fingerprint_type="exact",
        ).to_dict()

    # Perceptual hash for images
    if source_content_type.startswith("image/") or source_content_type == "":
        h1 = compute_perceptual_hash(source_bytes)
        h2 = compute_perceptual_hash(candidate_bytes)
        if h1 and h2:
            score = compute_similarity(h1, h2)
            return SimilarityResult(
                is_near_duplicate=score >= 90.0,
                similarity_score=score,
                fingerprint_type="perceptual",
            ).to_dict()

    return SimilarityResult(
        is_near_duplicate=False,
        similarity_score=0.0,
        fingerprint_type="sha256",
    ).to_dict()
