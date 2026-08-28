"""
Retrain image deepfake detector on FaceForensics++ dataset.

Usage:
  1. Get FaceForensics++ access: https://github.com/ondyari/faceforensics
  2. Download dataset: python dataset/remote_download.py -d data/ffpp -c c23 -t video -f 0
  3. Extract faces: python models/image/retrain_ffpp.py --extract
  4. Train: python models/image/retrain_ffpp.py --train
  5. Evaluate: python models/image/retrain_ffpp.py --eval

The script:
- Extracts face frames from FF++ videos using MTCNN or OpenCV
- Trains a CNN classifier on real vs manipulated faces
- Saves best model to models/image/weights/model_ffpp.pth
"""
import argparse
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms


# FaceForensics++ directory structure after download:
# data/ffpp/
#   original/     <- real videos
#   deepfakes/    <- face swap
#   face2face/    <- face reenactment
#   faceswap/     <- face swap (different method)
#   neuraltextures/ <- neural rendering

FFPP_DIR = Path("data/ffpp")
EXTRACTED_DIR = Path("data/ffpp_faces")
WEIGHTS_DIR = Path("models/image/weights")


class FaceExtractor:
    """Extract face frames from videos using OpenCV DNN face detector."""

    def __init__(self):
        # Use OpenCV's built-in face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def extract_faces_from_video(self, video_path: str, output_dir: str, max_frames: int = 10):
        """Extract face crops from a video file."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(int(fps / 2), 1)  # 2 FPS

        os.makedirs(output_dir, exist_ok=True)
        count = 0
        frame_idx = 0

        while cap.isOpened() and count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

                if len(faces) > 0:
                    # Take largest face
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    # Expand crop
                    pad = int(max(w, h) * 0.3)
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(frame.shape[1], x + w + pad)
                    y2 = min(frame.shape[0], y + h + pad)

                    face = frame[y1:y2, x1:x2]
                    face = cv2.resize(face, (224, 224))
                    cv2.imwrite(os.path.join(output_dir, f"frame_{count:04d}.jpg"), face)
                    count += 1

            frame_idx += 1

        cap.release()
        return count


class FFPPDataset(Dataset):
    """FaceForensics++ face dataset."""

    def __init__(self, root_dir: str, transform=None):
        self.root = Path(root_dir)
        self.transform = transform
        self.samples = []

        # Real faces
        real_dir = self.root / "real"
        if real_dir.exists():
            for img_path in real_dir.glob("*.jpg"):
                self.samples.append((str(img_path), 0))  # 0 = real

        # Fake faces
        fake_dir = self.root / "fake"
        if fake_dir.exists():
            for img_path in fake_dir.glob("*.jpg"):
                self.samples.append((str(img_path), 1))  # 1 = fake

        print(f"Loaded {len(self.samples)} samples ({sum(1 for _, l in self.samples if l == 0)} real, {sum(1 for _, l in self.samples if l == 1)} fake)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = __import__("PIL").Image.fromarray(img)

        if self.transform:
            img = self.transform(img)

        return img, label


class FaceCNN(nn.Module):
    """CNN for face deepfake detection — same architecture as existing model."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.4), nn.Linear(64, 2)
        )

    def forward(self, x):
        return self.classifier(self.features(x).flatten(1))


def extract_all_faces():
    """Extract faces from all FF++ videos."""
    extractor = FaceExtractor()

    # Process each manipulation type
    for subdir in ["original", "deepfakes", "face2face", "faceswap", "neuraltextures"]:
        src_dir = FFPP_DIR / subdir
        if not src_dir.exists():
            print(f"Skipping {subdir} — not found at {src_dir}")
            continue

        label = "real" if subdir == "original" else "fake"
        out_dir = EXTRACTED_DIR / label

        videos = list(src_dir.rglob("*.mp4"))[:200]  # Limit for speed
        print(f"Processing {subdir}: {len(videos)} videos → {label}")

        for i, video_path in enumerate(videos):
            output_dir = out_dir / f"{subdir}_{i:04d}"
            count = extractor.extract_faces_from_video(str(video_path), str(output_dir))
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(videos)} done ({count} faces/video)")

    print(f"Extraction complete. Faces at: {EXTRACTED_DIR}")


def train_model(epochs: int = 20, lr: float = 1e-3, batch_size: int = 32):
    """Train the face deepfake detector on extracted faces."""
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
    ])

    dataset = FFPPDataset(str(EXTRACTED_DIR), transform=transform)
    if len(dataset) == 0:
        print("No data found. Run --extract first.")
        return

    # Train/val split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FaceCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

    best_val_acc = 0

    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        # Validate
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        train_acc = 100.0 * train_correct / train_total
        val_acc = 100.0 * val_correct / val_total
        val_loss_avg = val_loss / len(val_loader)

        scheduler.step(val_loss_avg)

        print(f"Epoch {epoch + 1}/{epochs}: "
              f"train_loss={train_loss / len(train_loader):.4f} "
              f"train_acc={train_acc:.1f}% "
              f"val_loss={val_loss_avg:.4f} "
              f"val_acc={val_acc:.1f}%")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = WEIGHTS_DIR / "model_ffpp.pth"
            torch.save(model.state_dict(), save_path)
            print(f"  → Saved best model (val_acc={val_acc:.1f}%) to {save_path}")

    print(f"\nTraining complete. Best val_acc: {best_val_acc:.1f}%")
    print(f"Model saved to: {WEIGHTS_DIR / 'model_ffpp.pth'}")
    print(f"To use: the image model will auto-detect model_ffpp.pth")


def evaluate():
    """Evaluate the trained model on the validation set."""
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    dataset = FFPPDataset(str(EXTRACTED_DIR), transform=transform)
    loader = DataLoader(dataset, batch_size=64)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FaceCNN().to(device)

    weights_path = WEIGHTS_DIR / "model_ffpp.pth"
    if not weights_path.exists():
        print(f"No trained model found at {weights_path}. Run --train first.")
        return

    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.eval()

    correct = 0
    total = 0
    class_correct = [0, 0]
    class_total = [0, 0]

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)

            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            for i in range(2):
                class_total[i] += (labels == i).sum().item()
                class_correct[i] += ((predicted == i) & (labels == i)).sum().item()

    print(f"Overall accuracy: {100.0 * correct / total:.1f}%")
    print(f"Real accuracy: {100.0 * class_correct[0] / max(class_total[0], 1):.1f}%")
    print(f"Fake accuracy: {100.0 * class_correct[1] / max(class_total[1], 1):.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain deepfake detector on FaceForensics++")
    parser.add_argument("--extract", action="store_true", help="Extract faces from FF++ videos")
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--eval", action="store_true", help="Evaluate the model")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    if args.extract:
        extract_all_faces()
    elif args.train:
        train_model(epochs=args.epochs, lr=args.lr, batch_size=args.batch_size)
    elif args.eval:
        evaluate()
    else:
        parser.print_help()
