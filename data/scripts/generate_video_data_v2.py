"""
V2 Video data generator — realistic temporal patterns + deepfake artifacts.

Improvements:
- Face-like regions with smooth motion
- Realistic lighting and color variation
- Temporal artifacts: flickering, block glitches, frame inconsistency
- Higher resolution (128x128) for better feature learning

Usage:
    python data/scripts/generate_video_data_v2.py --n_per_class 100 --fps 10
"""

import argparse
import cv2
import numpy as np
from pathlib import Path


def _draw_face_region(frame, cx, cy, radius, base_color):
    """Draw a face-like oval with eye regions."""
    h, w = frame.shape[:2]
    # Face oval
    cv2.ellipse(frame, (cx, cy), (radius, int(radius * 1.3)), 0, 0, 360,
                tuple(int(c) for c in base_color), -1)
    # Eyes
    eye_y = cy - radius // 3
    for side in [-1, 1]:
        ex = cx + side * radius // 2
        cv2.circle(frame, (ex, eye_y), radius // 8, (40, 30, 25), -1)
        cv2.circle(frame, (ex, eye_y), radius // 14, (200, 200, 200), -1)


def generate_real_video(path, num_frames=30, size=128):
    """Realistic video: face region with smooth motion and lighting changes."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10, (size, size))

    # Random face params
    base_hue = np.random.randint(8, 22)
    base_sat = np.random.randint(40, 80)
    base_val = np.random.randint(140, 210)
    base_color = cv2.cvtColor(np.uint8([[[base_hue, base_sat, base_val]]]),
                              cv2.COLOR_HSV2BGR)[0, 0]

    cx_center = size // 2
    cy_center = size // 2
    radius = size // 4

    for i in range(num_frames):
        t = i / num_frames

        # Smooth motion (slight sway)
        cx = int(cx_center + 5 * np.sin(2 * np.pi * t * 0.5))
        cy = int(cy_center + 3 * np.cos(2 * np.pi * t * 0.3))

        # Lighting variation
        val_shift = int(15 * np.sin(2 * np.pi * t * 0.2))
        frame_color = np.clip(base_color.astype(int) + val_shift, 0, 255).astype(np.uint8)

        # Background gradient
        frame = np.zeros((size, size, 3), dtype=np.uint8)
        for c in range(3):
            bg_val = max(0, min(255, int(base_color[c]) - 60))
            frame[:, :, c] = np.linspace(bg_val - 10, bg_val + 10, size * size
                                         ).reshape(size, size).astype(np.uint8)

        # Draw face
        _draw_face_region(frame, cx, cy, radius, frame_color)

        # Natural noise
        noise = np.random.normal(0, 3, frame.shape).astype(np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        writer.write(frame)

    writer.release()


def generate_fake_video(path, num_frames=30, size=128):
    """Fake video with temporal artifacts: flickering, block glitches, frame inconsistency."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10, (size, size))

    base_hue = np.random.randint(8, 22)
    base_sat = np.random.randint(40, 80)
    base_val = np.random.randint(140, 210)

    # Choose artifact type
    artifact = np.random.choice(["flicker", "block", "inconsistent", "boundary"])

    for i in range(num_frames):
        t = i / num_frames

        # Base face (same as real)
        base_color = cv2.cvtColor(
            np.uint8([[[base_hue, base_sat, base_val]]]),
            cv2.COLOR_HSV2BGR)[0, 0]
        frame = np.zeros((size, size, 3), dtype=np.uint8)
        for c in range(3):
            bg_val = max(0, min(255, int(base_color[c]) - 60))
            frame[:, :, c] = np.linspace(bg_val - 10, bg_val + 10, size * size
                                         ).reshape(size, size).astype(np.uint8)

        cx = size // 2 + int(5 * np.sin(2 * np.pi * t * 0.5))
        cy = size // 2 + int(3 * np.cos(2 * np.pi * t * 0.3))
        _draw_face_region(frame, cx, cy, size // 4, base_color)

        # Apply artifact
        if artifact == "flicker":
            # Temporal flickering: brightness jumps
            if np.random.random() < 0.15:
                shift = np.random.randint(-40, 40, 3, dtype=np.int16)
                frame = np.clip(frame.astype(np.int16) + shift, 0, 255).astype(np.uint8)

        elif artifact == "block":
            # Block artifacts (simulating GAN upsampling)
            block = np.random.choice([8, 16])
            h, w = frame.shape[:2]
            for y in range(0, h, block):
                for x in range(0, w, block):
                    if np.random.random() < 0.2:
                        block_val = np.random.randint(0, 255, (1, 1, 3), dtype=np.uint8)
                        frame[y:y+block, x:x+block] = block_val

        elif artifact == "inconsistent":
            # Frame-to-frame color inconsistency
            shift = np.random.randint(-15, 15, 3, dtype=np.int16)
            frame = np.clip(frame.astype(np.int16) + shift, 0, 255).astype(np.uint8)

        elif artifact == "boundary":
            # Face-swap boundary seam
            mask = np.zeros((size, size), dtype=np.float32)
            r = np.random.randint(25, 45)
            cv2.circle(mask, (cx, cy), r, 1.0, -1)
            mask = cv2.GaussianBlur(mask, (11, 11), 3)
            shift = np.random.randint(-25, 25, 3, dtype=np.int16)
            shifted = np.clip(frame.astype(np.int16) + shift, 0, 255).astype(np.uint8)
            for c in range(3):
                frame[:, :, c] = (frame[:, :, c] * (1 - mask) +
                                  shifted[:, :, c] * mask).astype(np.uint8)

        writer.write(frame)

    writer.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_per_class", type=int, default=100)
    parser.add_argument("--output", type=str, default="data/video_synthetic_v2")
    parser.add_argument("--fps", type=int, default=10)
    args = parser.parse_args()

    output = Path(args.output)

    for split, n_mult in [("train", 1.0), ("val", 0.2), ("test", 0.2)]:
        n = max(1, int(args.n_per_class * n_mult))
        for label in ["real", "fake"]:
            d = output / split / label
            d.mkdir(parents=True, exist_ok=True)
            for i in range(n):
                path = d / f"{label}_{i:04d}.mp4"
                if label == "real":
                    generate_real_video(path, num_frames=30, size=128)
                else:
                    generate_fake_video(path, num_frames=30, size=128)
            print(f"  {split}/{label}: {n} videos")

    print(f"Done: {output}")


if __name__ == "__main__":
    main()
