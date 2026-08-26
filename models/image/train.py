"""
Phase 2 -- Train EfficientNet-B4 for image deepfake detection.

Usage: python -m models.image.train --epochs 2
"""

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torchvision import transforms
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, classification_report
from timm import create_model

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
    """Split image directory into train/val/test."""
    import random
    random.seed(42)

    real_files = sorted((data_dir / "real").glob("*.png"))
    fake_files = sorted((data_dir / "fake").glob("*.png"))

    all_files = [(str(f), 0) for f in real_files] + [(str(f), 1) for f in fake_files]
    random.shuffle(all_files)

    n = len(all_files)
    n_train = int(n * split_ratio[0])
    n_val = int(n * split_ratio[1])

    return (
        all_files[:n_train],
        all_files[n_train:n_train + n_val],
        all_files[n_train + n_val:],
    )


def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0
    preds, labels = [], []
    for imgs, lbls in loader:
        imgs, lbls = imgs.to(device), lbls.to(device)
        optimizer.zero_grad()
        out = model(imgs)
        loss = nn.functional.cross_entropy(out, lbls)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
        preds.extend(out.argmax(1).cpu().numpy())
        labels.extend(lbls.cpu().numpy())
    return total_loss / len(loader), accuracy_score(labels, preds), f1_score(labels, preds)


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    total_loss = 0
    preds, labels = [], []
    for imgs, lbls in loader:
        imgs, lbls = imgs.to(device), lbls.to(device)
        out = model(imgs)
        total_loss += nn.functional.cross_entropy(out, lbls).item()
        preds.extend(out.argmax(1).cpu().numpy())
        labels.extend(lbls.cpu().numpy())
    return total_loss / len(loader), accuracy_score(labels, preds), f1_score(labels, preds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--data_dir", type=str, default="data/processed/images")
    parser.add_argument("--max_samples", type=int, default=500)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir)

    # Augmentation (CV skill: proper transforms pipeline)
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # Load and split
    train_data, val_data, test_data = load_split(data_dir)
    if args.max_samples:
        train_data = train_data[:args.max_samples]

    print(f"Train: {len(train_data)} | Val: {len(val_data)} | Test: {len(test_data)}")

    train_ds = ImageDataset([f for f, _ in train_data], [l for _, l in train_data], train_tf)
    val_ds = ImageDataset([f for f, _ in val_data], [l for _, l in val_data], val_tf)
    test_ds = ImageDataset([f for f, _ in test_data], [l for _, l in test_data], val_tf)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    # Model: EfficientNet-B4 pretrained, replace head for 2 classes
    model = create_model("efficientnet_b4", pretrained=True, num_classes=2)
    model.to(device)

    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_f1 = 0
    print(f"\nTraining {args.epochs} epochs on {device}...\n")

    for epoch in range(args.epochs):
        train_loss, train_acc, train_f1 = train_epoch(model, train_loader, optimizer, device)
        val_loss, val_acc, val_f1 = evaluate(model, val_loader, device)
        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs}")
        print(f"  Train: loss={train_loss:.4f} acc={train_acc:.4f} f1={train_f1:.4f}")
        print(f"  Val:   loss={val_loss:.4f} acc={val_acc:.4f} f1={val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), WEIGHTS_DIR / "model.pth")
            print(f"  >> Saved (best F1={val_f1:.4f})")
        print()

    # Final test
    print("=" * 40)
    model.load_state_dict(torch.load(WEIGHTS_DIR / "model.pth", map_location=device))
    test_loss, test_acc, test_f1 = evaluate(model, test_loader, device)
    print(f"Test: loss={test_loss:.4f} acc={test_acc:.4f} f1={test_f1:.4f}")

    preds, labels = [], []
    model.eval()
    with torch.no_grad():
        for imgs, lbls in test_loader:
            out = model(imgs.to(device))
            preds.extend(out.argmax(1).cpu().numpy())
            labels.extend(lbls.numpy())
    print("\n" + classification_report(labels, preds, target_names=["real", "fake"]))
    print(f"Weights saved to {WEIGHTS_DIR}")


if __name__ == "__main__":
    main()
