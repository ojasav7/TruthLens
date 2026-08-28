"""Train Video V2 — CNN + Temporal Attention on V2 synthetic data."""

import sys
from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.video.model_v2 import VideoDeepfakeModelV2


class VideoDataset(Dataset):
    def __init__(self, root_dir, max_frames=10, transform=None):
        self.max_frames = max_frames
        self.transform = transform or transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.samples = []
        root = Path(root_dir)
        for label, label_idx in [("real", 0), ("fake", 1)]:
            label_dir = root / label
            if label_dir.exists():
                for p in label_dir.glob("*.mp4"):
                    self.samples.append((str(p), label_idx))

    def __len__(self):
        return len(self.samples)

    def _extract_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            return np.zeros((self.max_frames, 3, 224, 224), dtype=np.float32)
        step = max(total_frames // self.max_frames, 1)
        idx = 0
        while cap.isOpened() and len(frames) < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % step == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                tensor = self.transform(frame_rgb)
                frames.append(tensor.numpy())
            idx += 1
        cap.release()
        while len(frames) < self.max_frames:
            frames.append(frames[-1] if frames else np.zeros((3, 224, 224), dtype=np.float32))
        return np.stack(frames[:self.max_frames])

    def __getitem__(self, idx):
        video_path, label = self.samples[idx]
        frames = self._extract_frames(video_path)
        return torch.from_numpy(frames), torch.tensor(label, dtype=torch.long)


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    data_dir = Path("data/video_synthetic_v2")
    weights_dir = Path("models/video/weights")
    weights_dir.mkdir(parents=True, exist_ok=True)

    max_frames = 5
    batch_size = 8
    num_epochs = 5
    lr = 1e-3

    train_dataset = VideoDataset(data_dir / "train", max_frames=max_frames)
    val_dataset = VideoDataset(data_dir / "val", max_frames=max_frames)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")

    model = VideoDeepfakeModelV2(num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    best_val_acc = 0
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        correct = total = 0

        for videos, labels in train_loader:
            videos, labels = videos.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(videos)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += (logits.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)

        train_acc = correct / total
        avg_loss = total_loss / len(train_loader)

        model.eval()
        val_correct = val_total = 0
        with torch.no_grad():
            for videos, labels in val_loader:
                videos, labels = videos.to(device), labels.to(device)
                logits = model(videos)
                val_correct += (logits.argmax(dim=1) == labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_correct / val_total
        scheduler.step()

        print(f"Epoch {epoch+1}/{num_epochs}: loss={avg_loss:.4f}, train_acc={train_acc:.3f}, val_acc={val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), weights_dir / "model_v2.pth")
            print(f"  Saved (val_acc={val_acc:.3f})")

    print(f"Done. Best val_acc: {best_val_acc:.3f}")


if __name__ == "__main__":
    train()
