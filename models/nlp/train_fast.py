"""
Phase 1 — Fast BERT fake news training with DistilBERT.

DistilBERT is 40% smaller and 60% faster than BERT while retaining ~97% performance.
Perfect for CPU training and quick iteration.

Usage:
    python -m models.nlp.train_fast --epochs 2
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix


# --- Config ---
MODEL_NAME = "distilbert-base-uncased"
MAX_LEN = 128
WEIGHTS_DIR = Path("models/nlp/weights")


class FakeNewsDataset(Dataset):
    """CSV dataset with columns: text, label (fake/real)."""

    def __init__(self, csv_path: str, tokenizer, max_len: int = MAX_LEN):
        self.data = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append(row)
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.label_map = {"fake": 1, "real": 0}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data[idx]
        text = row["text"]
        label = self.label_map[row["label"]]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def train_epoch(model, dataloader, optimizer, scheduler, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        logits = outputs.logits

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=-1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average="binary")

    return avg_loss, accuracy, f1


def evaluate(model, dataloader, device):
    """Evaluate the model."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            logits = outputs.logits

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average="binary")

    return avg_loss, accuracy, f1, all_preds, all_labels


def main():
    parser = argparse.ArgumentParser(description="Train DistilBERT Fake News Classifier (fast)")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--max_len", type=int, default=MAX_LEN, help="Max sequence length")
    parser.add_argument("--train_csv", type=str, default="data/processed/nlp_train.csv")
    parser.add_argument("--val_csv", type=str, default="data/processed/nlp_val.csv")
    parser.add_argument("--test_csv", type=str, default="data/processed/nlp_test.csv")
    parser.add_argument("--max_train_samples", type=int, default=2000, help="Limit training samples for speed")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    print(f"Model: {MODEL_NAME} (DistilBERT — 40% smaller than BERT)")
    print(f"Config: epochs={args.epochs}, batch_size={args.batch_size}, lr={args.lr}")

    # Load tokenizer and model
    print(f"\nLoading {MODEL_NAME}...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    model.to(device)

    # Create datasets
    print("Loading datasets...")
    train_dataset = FakeNewsDataset(args.train_csv, tokenizer, args.max_len)
    val_dataset = FakeNewsDataset(args.val_csv, tokenizer, args.max_len)
    test_dataset = FakeNewsDataset(args.test_csv, tokenizer, args.max_len)

    # Optionally limit training samples for speed
    if args.max_train_samples and len(train_dataset) > args.max_train_samples:
        indices = torch.randperm(len(train_dataset))[:args.max_train_samples].tolist()
        train_dataset = torch.utils.data.Subset(train_dataset, indices)
        print(f"  Limited training to {len(train_dataset)} samples for speed")

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)

    print(f"Train: {len(train_dataset)} | Val: {len(val_dataset)} | Test: {len(test_dataset)}")

    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps
    )

    # Training loop
    best_val_f1 = 0.0
    print(f"\nStarting training for {args.epochs} epochs...\n")

    for epoch in range(args.epochs):
        print(f"Epoch {epoch + 1}/{args.epochs}")
        print("-" * 40)

        train_loss, train_acc, train_f1 = train_epoch(model, train_loader, optimizer, scheduler, device)
        val_loss, val_acc, val_f1, _, _ = evaluate(model, val_loader, device)

        print(f"  Train  -- Loss: {train_loss:.4f} | Acc: {train_acc:.4f} | F1: {train_f1:.4f}")
        print(f"  Val    -- Loss: {val_loss:.4f} | Acc: {val_acc:.4f} | F1: {val_f1:.4f}")

        # Save best model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(str(WEIGHTS_DIR))
            tokenizer.save_pretrained(str(WEIGHTS_DIR))
            print(f"  >> New best model saved (F1: {val_f1:.4f})")
        print()

    # Final test evaluation
    print("=" * 40)
    print("FINAL TEST EVALUATION")
    print("=" * 40)

    # Load best model for final eval
    model = DistilBertForSequenceClassification.from_pretrained(str(WEIGHTS_DIR))
    model.to(device)

    test_loss, test_acc, test_f1, preds, labels = evaluate(model, test_loader, device)
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test F1: {test_f1:.4f}")
    print()
    print("Classification Report:")
    print(classification_report(labels, preds, target_names=["real", "fake"]))
    print("Confusion Matrix:")
    print(confusion_matrix(labels, preds))

    # Save training metadata
    meta_path = WEIGHTS_DIR / "training_meta.txt"
    with open(meta_path, "w") as f:
        f.write(f"Model: {MODEL_NAME}\n")
        f.write(f"Epochs: {args.epochs}\n")
        f.write(f"Batch size: {args.batch_size}\n")
        f.write(f"Learning rate: {args.lr}\n")
        f.write(f"Train size: {len(train_dataset)}\n")
        f.write(f"Val size: {len(val_dataset)}\n")
        f.write(f"Test size: {len(test_dataset)}\n")
        f.write(f"Test Accuracy: {test_acc:.4f}\n")
        f.write(f"Test F1: {test_f1:.4f}\n")
        f.write(f"Device: {device}\n")
    print(f"\nTraining metadata saved to {meta_path}")
    print(f"\nDone! Weights saved to {WEIGHTS_DIR}")


if __name__ == "__main__":
    main()
