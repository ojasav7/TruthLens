"""Generate synthetic video dataset for video deepfake detection.

Creates short videos with distinct patterns:
- Real: smooth gradients, natural motion (sine wave movement)
- Fake: sharp edges, block artifacts, inconsistent frames
"""

import cv2
import numpy as np
from pathlib import Path


def generate_real_video(path: Path, num_frames: int = 30, size: int = 64):
    """Generate a 'real' video with smooth motion."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10, (size, size))
    
    y_coords, x_coords = np.meshgrid(np.arange(size), np.arange(size), indexing='ij')
    
    for i in range(num_frames):
        t = i / num_frames
        frame = np.zeros((size, size, 3), dtype=np.uint8)
        frame[:, :, 0] = (128 + 60 * np.sin(2 * np.pi * (x_coords / size + t))).astype(np.uint8)
        frame[:, :, 1] = (128 + 60 * np.cos(2 * np.pi * (y_coords / size + t))).astype(np.uint8)
        frame[:, :, 2] = (128 + 40 * np.sin(2 * np.pi * ((x_coords + y_coords) / size + t))).astype(np.uint8)
        writer.write(frame)
    
    writer.release()


def generate_fake_video(path: Path, num_frames: int = 30, size: int = 64):
    """Generate a 'fake' video with block artifacts."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10, (size, size))
    
    for i in range(num_frames):
        frame = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
        # Block artifacts via vectorized subsampling
        block_size = 8
        mask = np.random.random((size // block_size, size // block_size)) > 0.7
        mask = np.repeat(np.repeat(mask, block_size, axis=0), block_size, axis=1)
        colors = np.random.randint(0, 255, (size // block_size, size // block_size, 3), dtype=np.uint8)
        colors = np.repeat(np.repeat(colors, block_size, axis=0), block_size, axis=1)
        frame[mask] = colors[mask]
        writer.write(frame)
    
    writer.release()


def main(output_dir: str = "data/video_synthetic", num_per_class: int = 50):
    """Generate synthetic video dataset."""
    output_path = Path(output_dir)
    
    for split in ["train", "val", "test"]:
        for label in ["real", "fake"]:
            dir_path = output_path / split / label
            dir_path.mkdir(parents=True, exist_ok=True)
            
            num_videos = num_per_class if split == "train" else num_per_class // 5
            
            for i in range(num_videos):
                video_path = dir_path / f"{label}_{i:04d}.mp4"
                if label == "real":
                    generate_real_video(video_path)
                else:
                    generate_fake_video(video_path)
            
            print(f"Generated {num_videos} {label} videos in {split}/")


if __name__ == "__main__":
    main()
