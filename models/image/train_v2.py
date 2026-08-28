"""Train Image V2 — EfficientNet-B4 backbone + improved classifier head."""

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--data_dir", type=str, default="data/processed/images")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = Path(args.data_dir)

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.RandomAffine(degrees=5, translate=(0.05, 0.05)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
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

    # Model: EfficientNet-B4 backbone + improved head
    backbone = create_model("efficientnet_b4", pretrained=True, num_classes=0)
    feat_dim = backbone.num_features
    classifier = nn.Sequential(
        nn.Linear(feat_dim, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.2),
        nn.Linear(128, 2),
    )

    backbone.to(device)
    classifier.to(device)

    params = list(backbone.parameters()) + list(classifier.parameters())
    optimizer = AdamW(params, lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()

    best_f1 = 0
    print(f"\nTraining {args.epochs} epochs on {device}...\n")

    for epoch in range(args.epochs):
        backbone.train()
        classifier.train()
        total_loss = 0
        preds, labels = [], []

        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            features = backbone(imgs)
            logits = classifier(features)
            loss = criterion(logits, lbls)
            loss.backward()
            nn.utils.clip_grad_norm_(params, 1.0)
            optimizer.step()
            total_loss += loss.item()
            preds.extend(logits.argmax(1).cpu().numpy())
            labels.extend(lbls.cpu().numpy())

        train_acc = accuracy_score(labels, preds)
        train_f1 = f1_score(labels, preds)

        # Validate
        backbone.eval()
        classifier.eval()
        val_preds, val_labels = [], []
        val_loss = 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                features = backbone(imgs)
                logits = classifier(features)
                val_loss += criterion(logits, lbls).item()
                val_preds.extend(logits.argmax(1).cpu().numpy())
                val_labels.extend(lbls.cpu().numpy())

        val_acc = accuracy_score(val_labels, val_preds)
        val_f1 = f1_score(val_labels, val_preds)
        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs}")
        print(f"  Train: loss={total_loss/len(train_loader):.4f} acc={train_acc:.4f} f1={train_f1:.4f}")
        print(f"  Val:   loss={val_loss/len(val_loader):.4f} acc={val_acc:.4f} f1={val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
            torch.save({
                "backbone": backbone.state_dict(),
                "classifier": classifier.state_dict(),
            }, WEIGHTS_DIR / "model_v2.pth")
            print(f"  >> Saved (best F1={val_f1:.4f})")
        print()

    # Final test
    print("=" * 40)
    state = torch.load(WEIGHTS_DIR / "model_v2.pth", map_location=device)
    backbone.load_state_dict(state["backbone"])
    classifier.load_state_dict(state["classifier"])
    backbone.eval()
    classifier.eval()

    test_preds, test_labels = [], []
    with torch.no_grad():
        for imgs, lbls in test_loader:
            features = backbone(imgs.to(device))
            logits = classifier(features)
            test_preds.extend(logits.argmax(1).cpu().numpy())
            test_labels.extend(lbls.numpy())

    print(f"Test acc: {accuracy_score(test_labels, test_preds):.4f}")
    print(f"Test f1:  {f1_score(test_labels, test_preds):.4f}")
    print("\n" + classification_report(test_labels, test_preds, target_names=["real", "fake"]))


if __name__ == "__main__":
    main()
