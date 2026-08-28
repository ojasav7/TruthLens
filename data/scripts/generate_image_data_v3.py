"""
V3 Image data generator — much more distinctive deepfake artifacts.

The V2 artifacts were too subtle. V3 uses:
- Heavy JPEG compression (quality 3-15)
- Visible color channel shifts
- Block boundary artifacts
- Strong Gaussian noise
- Sharp edges from copy-paste boundaries
- Spectral patterns from frequency manipulation

Usage: python data/scripts/generate_image_data_v3.py --n_per_class 3000
"""
import argparse
import numpy as np
import cv2
from pathlib import Path

SEED = 42
np.random.seed(SEED)


def _random_face(size=224):
    """Generate a realistic face-like image."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    hue = np.random.randint(8, 22)
    sat = np.random.randint(40, 80)
    val = np.random.randint(140, 210)
    base = cv2.cvtColor(np.uint8([[[hue, sat, val]]]), cv2.COLOR_HSV2BGR)[0, 0]

    for c in range(3):
        grad = np.linspace(
            max(0, int(base[c]) - 25), min(255, int(base[c]) + 25), size * size
        ).reshape(size, size).astype(np.uint8)
        img[:, :, c] = grad

    cx = size // 2 + np.random.randint(-10, 10)
    cy = size // 2 + np.random.randint(-10, 10)
    axes = (size // 3 + np.random.randint(-5, 5), size // 2 - 5 + np.random.randint(-5, 5))
    cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, tuple(int(c) for c in base), -1)

    eye_y = cy - size // 8
    eye_spread = size // 6
    for ex in [cx - eye_spread, cx + eye_spread]:
        cv2.ellipse(img, (ex, eye_y), (size // 16, size // 20), 0, 0, 360,
                    tuple(max(0, int(c) - 50) for c in base), -1)
        cv2.circle(img, (ex, eye_y), size // 28, (240, 240, 240), -1)
        cv2.circle(img, (ex + np.random.randint(-2, 2), eye_y), size // 50, (30, 20, 15), -1)

    mouth_y = cy + size // 5
    cv2.ellipse(img, (cx, mouth_y), (size // 6, size // 30), 0, 0, 180,
                tuple(max(0, int(c) - 30) for c in base), 2)

    img = cv2.GaussianBlur(img, (3, 3), 0.5)
    noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def _fake_heavy_compression(img):
    """Extreme JPEG compression — very visible blocking artifacts."""
    quality = np.random.randint(3, 12)
    _, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imdecode(encoded, cv2.IMREAD_COLOR)


def _fake_color_shift(img):
    """Shuffle/shift color channels — breaks natural color relationships."""
    fake = img.copy()
    shift = np.random.randint(-40, 40, 3).astype(np.int16)
    for c in range(3):
        fake[:, :, c] = np.clip(fake[:, :, c].astype(np.int16) + shift[c], 0, 255).astype(np.uint8)
    # Swap two channels with 50% probability
    if np.random.random() < 0.5:
        c1, c2 = np.random.choice(3, 2, replace=False)
        fake[:, :, [c1, c2]] = fake[:, :, [c2, c1]]
    return fake


def _fake_block_artifact(img):
    """Visible block boundary artifacts (simulates GAN upsampling)."""
    fake = img.copy()
    h, w = fake.shape[:2]
    block = np.random.choice([8, 16])
    for y in range(0, h, block):
        for x in range(0, w, block):
            if np.random.random() < 0.4:
                patch = fake[y:y+block, x:x+block].copy()
                shift = np.random.randint(-30, 30, (1, 1, 3), dtype=np.int16)
                fake[y:y+block, x:x+block] = np.clip(
                    patch.astype(np.int16) + shift, 0, 255
                ).astype(np.uint8)
    return fake


def _fake_noise_injection(img):
    """Heavy Gaussian noise — simulates low-quality generation."""
    fake = img.copy()
    sigma = np.random.uniform(15, 35)
    noise = np.random.normal(0, sigma, fake.shape).astype(np.float32)
    fake = np.clip(fake.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return fake


def _fake_face_swap_boundary(img):
    """Visible face-swap boundary with seam line."""
    fake = img.copy()
    h, w = fake.shape[:2]
    cx = w // 2 + np.random.randint(-15, 15)
    cy = h // 2 + np.random.randint(-10, 10)
    radius = np.random.randint(40, 70)

    mask = np.zeros((h, w), dtype=np.float32)
    cv2.circle(mask, (cx, cy), radius, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (21, 21), 7)

    shift = np.random.randint(-35, 35, 3).astype(np.int16)
    shifted = np.clip(fake.astype(np.int16) + shift, 0, 255).astype(np.uint8)
    for c in range(3):
        fake[:, :, c] = (fake[:, :, c] * (1 - mask) + shifted[:, :, c] * mask).astype(np.uint8)

    # Visible seam
    cv2.circle(fake, (cx, cy), radius, (255, 255, 255), 2)
    return fake


def _fake_spectral_pattern(img):
    """Strong periodic pattern (simulates frequency-domain GAN artifacts)."""
    fake = img.copy()
    h, w = fake.shape[:2]
    freq_x = np.random.uniform(0.03, 0.12)
    freq_y = np.random.uniform(0.03, 0.12)
    phase = np.random.uniform(0, 2 * np.pi)
    amp = np.random.uniform(8, 20)
    pattern = np.sin(
        2 * np.pi * freq_x * np.arange(w)[None, :] +
        2 * np.pi * freq_y * np.arange(h)[:, None] + phase
    ) * amp
    fake = np.clip(fake.astype(np.float32) + pattern[:, :, None], 0, 255).astype(np.uint8)
    return fake


def _fake_selective_blur(img):
    """Strong blur in facial region — simulates blending artifact."""
    fake = img.copy()
    h, w = fake.shape[:2]
    k = np.random.choice([25, 35, 51])
    blurred = cv2.GaussianBlur(fake, (k, k), 0)
    mask = np.zeros((h, w), dtype=np.float32)
    cx = np.random.randint(60, w - 60)
    cy = np.random.randint(60, h - 60)
    rx = np.random.randint(25, 60)
    ry = np.random.randint(25, 50)
    cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (21, 21), 7)
    for c in range(3):
        fake[:, :, c] = (fake[:, :, c] * (1 - mask) + blurred[:, :, c] * mask).astype(np.uint8)
    return fake


def _apply_distinctive_fake(img):
    """Apply 1-2 distinctive artifacts."""
    methods = [
        _fake_heavy_compression,
        _fake_color_shift,
        _fake_block_artifact,
        _fake_noise_injection,
        _fake_face_swap_boundary,
        _fake_spectral_pattern,
        _fake_selective_blur,
    ]
    method = np.random.choice(methods)
    fake = method(img)
    # Stack 1-2 more artifacts for maximum distinctiveness
    n_extra = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
    for _ in range(n_extra):
        extra = np.random.choice([m for m in methods if m != method])
        fake = extra(fake)
    return fake


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_per_class", type=int, default=3000)
    parser.add_argument("--output", type=str, default="data/processed/images_v3")
    args = parser.parse_args()

    output = Path(args.output)
    real_dir = output / "real"
    fake_dir = output / "fake"
    real_dir.mkdir(parents=True, exist_ok=True)
    fake_dir.mkdir(parents=True, exist_ok=True)

    n = args.n_per_class
    print(f"Generating {n} real + {n} fake images with distinctive artifacts...")

    for i in range(n):
        img = _random_face(224)
        cv2.imwrite(str(real_dir / f"{i:04d}.png"), img)

        fake = _apply_distinctive_fake(img)
        cv2.imwrite(str(fake_dir / f"{i:04d}.png"), fake)

        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{n}")

    print(f"Done: {len(list(real_dir.glob('*.png')))} real, {len(list(fake_dir.glob('*.png')))} fake")


if __name__ == "__main__":
    main()
