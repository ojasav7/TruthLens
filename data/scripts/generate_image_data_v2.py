"""
V2 Image data generator — realistic face-like patterns + deepfake artifacts.

Improvements over V1:
- More realistic face structure (skin gradients, eye regions, nose bridge, mouth)
- Better fake artifacts: face-swap boundary, GAN checkerboard, spectral patterns
- Varied face sizes and positions
- Natural noise and lighting variation

Usage:
    python data/scripts/generate_image_data_v2.py --n_per_class 1500
"""

import argparse
import numpy as np
import cv2
from pathlib import Path

SEED = 42
np.random.seed(SEED)


def _random_face(size=224):
    """Generate a realistic face-like image with skin tones, eyes, nose, mouth."""
    img = np.zeros((size, size, 3), dtype=np.uint8)

    # Skin tone: warm HSV range
    hue = np.random.randint(8, 22)
    sat = np.random.randint(40, 80)
    val = np.random.randint(140, 210)
    base = cv2.cvtColor(np.uint8([[[hue, sat, val]]]), cv2.COLOR_HSV2BGR)[0, 0]

    # Gradient fill (lighting variation)
    for c in range(3):
        grad = np.linspace(
            max(0, int(base[c]) - 25),
            min(255, int(base[c]) + 25),
            size * size,
        ).reshape(size, size).astype(np.uint8)
        img[:, :, c] = grad

    # Face oval
    cx = size // 2 + np.random.randint(-10, 10)
    cy = size // 2 + np.random.randint(-10, 10)
    axes = (size // 3 + np.random.randint(-5, 5), size // 2 - 5 + np.random.randint(-5, 5))
    cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, tuple(int(c) for c in base), -1)

    # Eye sockets (darker areas)
    eye_y = cy - size // 8
    eye_spread = size // 6
    for ex in [cx - eye_spread, cx + eye_spread]:
        cv2.ellipse(img, (ex, eye_y), (size // 16, size // 20), 0, 0, 360,
                    tuple(max(0, int(c) - 50) for c in base), -1)
        # Eyeball
        cv2.circle(img, (ex, eye_y), size // 28, (240, 240, 240), -1)
        # Pupil
        pupil_r = size // 50
        cv2.circle(img, (ex + np.random.randint(-2, 2), eye_y), pupil_r, (30, 20, 15), -1)

    # Nose bridge highlight
    nose_pts = [(cx, cy - size // 8), (cx + 2, cy), (cx, cy + size // 10)]
    for i in range(len(nose_pts) - 1):
        cv2.line(img, nose_pts[i], nose_pts[i + 1],
                 tuple(min(255, int(c) + 35) for c in base), 2)

    # Mouth
    mouth_y = cy + size // 5
    mouth_w = size // 6
    cv2.ellipse(img, (cx, mouth_y), (mouth_w, size // 30), 0, 0, 180,
                tuple(max(0, int(c) - 30) for c in base), 2)

    # Cheek highlights
    for side in [-1, 1]:
        cheek_x = cx + side * size // 4
        cheek_y = cy + size // 10
        cv2.circle(img, (cheek_x, cheek_y), size // 12,
                   tuple(min(255, int(c) + 15) for c in base), -1)

    # Natural Gaussian blur
    img = cv2.GaussianBlur(img, (3, 3), 0.5)

    # Sensor noise
    noise = np.random.normal(0, 4, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img


def _fake_face_swap_boundary(img):
    """Simulate face-swap boundary artifact — the most common deepfake tell."""
    fake = img.copy()
    h, w = fake.shape[:2]
    cx, cy = w // 2 + np.random.randint(-15, 15), h // 2 + np.random.randint(-10, 10)
    radius = np.random.randint(35, 65)

    # Create smooth circular mask for the swapped region
    mask = np.zeros((h, w), dtype=np.float32)
    cv2.circle(mask, (cx, cy), radius, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (21, 21), 7)

    # Shift the swapped region color slightly
    shift = np.random.randint(-20, 20, 3).astype(np.int16)
    shifted = np.clip(fake.astype(np.int16) + shift, 0, 255).astype(np.uint8)

    # Blend: original outside, shifted inside
    for c in range(3):
        fake[:, :, c] = (fake[:, :, c] * (1 - mask) + shifted[:, :, c] * mask).astype(np.uint8)

    # Add visible seam line (boundary artifact)
    base_pixel = np.clip(fake[cy, cx].astype(int) + 40, 0, 255)
    seam_color = tuple(int(c) for c in base_pixel)
    cv2.circle(fake, (cx, cy), radius, seam_color, 1)

    return fake


def _fake_gan_checkerboard(img):
    """Simulate GAN checkerboard upsampling artifact."""
    fake = img.copy()
    h, w = fake.shape[:2]
    block = np.random.choice([4, 6, 8])
    noise_amp = np.random.uniform(3, 12)

    for y in range(0, h, block):
        for x in range(0, w, block):
            if (y // block + x // block) % 2 == 0:
                patch = fake[y:y+block, x:x+block]
                shift = np.random.randint(-int(noise_amp), int(noise_amp), patch.shape, dtype=np.int16)
                fake[y:y+block, x:x+block] = np.clip(patch.astype(np.int16) + shift, 0, 255).astype(np.uint8)

    return fake


def _fake_spectral_noise(img):
    """Simulate frequency-domain artifacts from GAN generation."""
    fake = img.copy()
    # Add periodic noise pattern (simulates spectral leakage from GAN)
    h, w = fake.shape[:2]
    freq = np.random.uniform(0.05, 0.15)
    phase = np.random.uniform(0, 2 * np.pi)
    pattern = np.sin(2 * np.pi * freq * np.arange(h)[:, None] + phase) * np.random.uniform(3, 8)
    pattern = np.repeat(pattern, w, axis=1)[:, :, None]
    fake = np.clip(fake.astype(np.float32) + pattern, 0, 255).astype(np.uint8)
    return fake


def _fake_compression(img):
    """Heavy JPEG compression with specific quality to create artifacts."""
    quality = np.random.randint(5, 25)
    _, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imdecode(encoded, cv2.IMREAD_COLOR)


def _fake_selective_blur(img):
    """Blur specific facial regions (simulates face-swap blending)."""
    fake = img.copy()
    h, w = fake.shape[:2]
    k = np.random.choice([15, 21, 31])
    blurred = cv2.GaussianBlur(fake, (k, k), 0)

    mask = np.zeros((h, w), dtype=np.float32)
    cx, cy = np.random.randint(60, w - 60), np.random.randint(60, h - 60)
    rx, ry = np.random.randint(20, 50), np.random.randint(20, 40)
    cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (21, 21), 7)

    for c in range(3):
        fake[:, :, c] = (fake[:, :, c] * (1 - mask) + blurred[:, :, c] * mask).astype(np.uint8)

    return fake


def _apply_random_fake(img):
    """Apply one of several deepfake artifact types."""
    methods = [
        _fake_face_swap_boundary,
        _fake_gan_checkerboard,
        _fake_spectral_noise,
        _fake_compression,
        _fake_selective_blur,
    ]
    # Sometimes stack 2 artifacts
    method = np.random.choice(methods)
    fake = method(img)
    if np.random.random() < 0.3:
        second = np.random.choice([m for m in methods if m != method])
        fake = second(fake)
    return fake


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_per_class", type=int, default=1500)
    parser.add_argument("--output", type=str, default="data/processed/images")
    args = parser.parse_args()

    output = Path(args.output)
    real_dir = output / "real"
    fake_dir = output / "fake"
    real_dir.mkdir(parents=True, exist_ok=True)
    fake_dir.mkdir(parents=True, exist_ok=True)

    n = args.n_per_class
    print(f"Generating {n} real + {n} fake images...")

    for i in range(n):
        img = _random_face(224)
        cv2.imwrite(str(real_dir / f"{i:04d}.png"), img)

        fake = _apply_random_fake(img)
        cv2.imwrite(str(fake_dir / f"{i:04d}.png"), fake)

        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{n}")

    print(f"Done: {len(list(real_dir.glob('*.png')))} real, {len(list(fake_dir.glob('*.png')))} fake")


if __name__ == "__main__":
    main()
