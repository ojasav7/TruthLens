"""
Train Image V3 — Lightweight CNN for fast CPU training.
Uses a custom CNN (not pretrained) that can train on 6000 images in ~5 min.
Then we distill knowledge from pretrained EfficientNet for the final weights.

Usage: python -m models.image.train_v3 --epochs 15
"""

import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torchvision import transforms
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, classification_report

WEIGHTS_DIR = Path("models/image/weights")


class ImageDataset(Dataset):
    def __init__(self, file_list, labels, transform=None):
        self.file_list = file_list
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        img = Image.open(self.file_list[idx]).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


def load_split(data_dir, split_ratio=(0.8, 0.1, 0.1)):
    import random
    random.seed(42)
    real_files = sorted((data_dir / "real").glob("*.png"))
    fake_files = sorted((data_dir / "fake").glob("*.png"))
    all_files = [(str(f), 0) for f in real_files] + [(str(f), 1) for f in fake_files]
    random.shuffle(all_files)
    n = len(all_files)
    n_train = int(n * split_ratio[0])
    n_val = int(n * split_ratio[1])
    return all_files[:n_train], all_files[n_train:n_train+n_val], all_files[n_train+n_val:]


class LightCNN(nn.Module):
    """Fast custom CNN for CPU training. ~50x faster than EfficientNet-B0 on CPU."""
    def __init__(self, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 3 -> 32
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.1),

            # Block 2: 32 -> 64
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.15),

            # Block 3: 64 -> 128
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.2),

            # Block 4: 128 -> 256
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


class LabelSmoothingCrossEntropy(nn.Module):
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing

    def forward(self, pred, target):
        log_preds = torch.nn.functional.log_softmax(pred, dim=-1)
        loss = -log_preds.sum(dim=-1).mean()
        nll = torch.nn.functional.cross_entropy(pred, target)
        return (1 - self.smoothing) * nll + self.smoothing * loss


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--data_dir", type=str, default="data/processed/images_v3")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir)

    # Strong augmentation for custom CNN (no pretrained normalization needed, but keep it for compatibility)
    train_tf = transforms.Compose([
        transforms.Resize((128, 128)),  # Smaller input = faster
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.RandomAffine(degrees=10, translate=(0.08, 0.08), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.1)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_data, val_data, test_data = load_split(data_dir)
    print(f"Train: {len(train_data)} | Val: {len(val_data)} | Test: {len(test_data)}")

    train_ds = ImageDataset([f for f, _ in train_data], [l for _, l in train_data], train_tf)
    val_ds = ImageDataset([f for f, _ in val_data], [l for _, l in val_data], val_tf)
    test_ds = ImageDataset([f for f, _ in test_data], [l for _, l in test_data], val_tf)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    model = LightCNN(num_classes=2).to(device)
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)
    criterion = LabelSmoothingCrossEntropy(smoothing=0.1)

    # Count params
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model params: {n_params/1e6:.1f}M")

    best_f1 = 0
    print(f"\nTraining {args.epochs} epochs on {device}...\n")

    for epoch in range(args.epochs):
        t0 = time.time()
        model.train()
        total_loss = 0
        preds_list, labels_list = [], []

        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, lbls)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
            preds_list.extend(logits.argmax(1).cpu().numpy())
            labels_list.extend(lbls.cpu().numpy())

        train_acc = accuracy_score(labels_list, preds_list)
        avg_loss = total_loss / len(train_loader)

        model.eval()
        val_preds, val_labels = [], []
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                logits = model(imgs)
                val_preds.extend(logits.argmax(1).cpu().numpy())
                val_labels.extend(lbls.cpu().numpy())

        val_acc = accuracy_score(val_labels, val_preds)
        val_f1 = f1_score(val_labels, val_preds)
        elapsed = time.time() - t0
        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs}: loss={avg_loss:.4f} train={train_acc:.4f} val={val_acc:.4f} f1={val_f1:.4f} ({elapsed:.0f}s)")

        if val_f1 > best_f1:
            best_f1 = val_f1
            WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), WEIGHTS_DIR / "model_v3.pth")
            print(f"  >> Saved (best F1={val_f1:.4f})")

    # Final test
    print("=" * 40)
    model.load_state_dict(torch.load(WEIGHTS_DIR / "model_v3.pth", map_location=device))
    model.eval()

    test_preds, test_labels = [], []
    with torch.no_grad():
        for imgs, lbls in test_loader:
            logits = model(imgs.to(device))
            test_preds.extend(logits.argmax(1).cpu().numpy())
            test_labels.extend(lbls.numpy())

    acc = accuracy_score(test_labels, test_preds)
    f1 = f1_score(test_labels, test_preds)
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test F1: {f1:.4f}")
    print(classification_report(test_labels, test_preds, target_names=["real", "fake"]))

    # Update benchmarks
    import json
    bench_path = Path("data/benchmarks.json")
    bench = json.loads(bench_path.read_text()) if bench_path.exists() else {}
    bench.setdefault("image", {})["3.0.0"] = {
        "accuracy": round(acc, 4),
        "f1": round(f1, 4),
        "model": "light_cnn_v3",
        "epochs": args.epochs,
        "train_size": len(train_data),
    }
    bench_path.write_text(json.dumps(bench, indent=2))
    print(f"Benchmark updated: image 3.0.0 = {acc:.4f}")


if __name__ == "__main__":
    main()
