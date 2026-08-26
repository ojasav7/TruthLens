"""
Phase 2 -- Generate synthetic real/fake image dataset.

Real: face-like patterns with natural variation (smooth gradients, skin tones).
Fake: same patterns with synthetic artifacts (compression blocks, color shift, noise).

Ponytail: generates enough for a working prototype. Swap with real FaceForensics++ later.
"""

import numpy as np
import cv2
from pathlib import Path

SEED = 42
np.random.seed(SEED)

OUTPUT = Path("data/processed/images")
REAL_DIR = OUTPUT / "real"
FAKE_DIR = OUTPUT / "fake"


def _random_face_like(size=224):
    """Generate a face-like pattern with skin tones and smooth gradients."""
    img = np.zeros((size, size, 3), dtype=np.uint8)

    # Skin tone base
    hue = np.random.randint(8, 25)
    sat = np.random.randint(40, 80)
    val = np.random.randint(140, 220)
    base_color = cv2.cvtColor(np.uint8([[[hue, sat, val]]]), cv2.COLOR_HSV2BGR)[0, 0]

    # Fill with gradient
    for c in range(3):
        gradient = np.linspace(
            int(base_color[c]) - 30,
            int(base_color[c]) + 30,
            size * size,
        ).reshape(size, size).astype(np.uint8)
        img[:, :, c] = gradient

    # Add face-like oval (simulating face shape)
    cx, cy = size // 2, size // 2
    axes = (size // 3, size // 2 - 10)
    cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, tuple(int(c) for c in base_color), -1)

    # Add "eyes" -- dark circles
    eye_y = cy - size // 8
    for ex in [cx - size // 6, cx + size // 6]:
        cv2.circle(img, (ex, eye_y), size // 20, (30, 20, 15), -1)

    # Add nose bridge highlight
    cv2.line(img, (cx, cy - size // 6), (cx, cy + size // 6),
             tuple(min(255, int(c) + 40) for c in base_color), 3)

    # Add slight Gaussian blur for natural look
    img = cv2.GaussianBlur(img, (3, 3), 0.5)

    # Add natural noise
    noise = np.random.normal(0, 5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img


def _make_fake(img):
    """Apply synthetic deepfake artifacts to an image."""
    fake = img.copy()
    method = np.random.choice(["jpeg", "color_shift", "noise", "block", "blur"])

    if method == "jpeg":
        # Heavy JPEG compression artifacts
        _, encoded = cv2.imencode(".jpg", fake, [cv2.IMWRITE_JPEG_QUALITY, 8])
        fake = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

    elif method == "color_shift":
        # Unnatural color channel shift
        shift = np.random.randint(-30, 30, 3).astype(np.int16)
        fake = np.clip(fake.astype(np.int16) + shift, 0, 255).astype(np.uint8)

    elif method == "noise":
        # Heavy salt-and-pepper noise
        prob = np.random.uniform(0.02, 0.08)
        mask = np.random.random(fake.shape[:2])
        fake[mask < prob] = 0
        fake[mask > 1 - prob] = 255

    elif method == "block":
        # Block artifacts (simulating GAN checkerboard)
        block = np.random.randint(4, 12)
        h, w = fake.shape[:2]
        for y in range(0, h, block):
            for x in range(0, w, block):
                if np.random.random() < 0.3:
                    fake[y:y+block, x:x+block] = np.random.randint(0, 255, (1, 1, 3), dtype=np.uint8)

    elif method == "blur":
        # Selective blur (simulating face-swap boundary)
        k = np.random.choice([15, 21, 31])
        blurred = cv2.GaussianBlur(fake, (k, k), 0)
        mask = np.zeros(fake.shape[:2], dtype=np.float32)
        cx, cy = np.random.randint(50, 174, 2)
        cv2.circle(mask, (cx, cy), np.random.randint(30, 60), 1.0, -1)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        fake = (fake * (1 - mask[:, :, None]) + blurred * mask[:, :, None]).astype(np.uint8)

    return fake


def main():
    n_per_class = 1000

    for d in [REAL_DIR, FAKE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Generating {n_per_class} real + {n_per_class} fake images...")

    for i in range(n_per_class):
        img = _random_face_like(224)
        cv2.imwrite(str(REAL_DIR / f"{i:04d}.png"), img)

        fake = _make_fake(img)
        cv2.imwrite(str(FAKE_DIR / f"{i:04d}.png"), fake)

        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{n_per_class} done")

    print(f"Saved to {OUTPUT}")
    print(f"  Real: {len(list(REAL_DIR.glob('*.png')))} images")
    print(f"  Fake: {len(list(FAKE_DIR.glob('*.png')))} images")


if __name__ == "__main__":
    main()
