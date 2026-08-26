"""Train audio voice clone classifier — MFCC features + small MLP.

Ponytail: MFCC features are ~50x faster than Wav2Vec2 on CPU, and on
synthetic data the accuracy is comparable. Use Wav2Vec2 in production
if needed (swap the feature extractor, keep the head architecture).
"""

import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from torchaudio.transforms import MFCC
import numpy as np
import soundfile as sf

# --- Config ---
DATA_DIR = Path("data/audio")
WEIGHTS_DIR = Path("models/audio/weights")
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
MAX_LEN = 16000 * 2  # 2 seconds at 16kHz
N_MFCC = 40
BATCH_SIZE = 16
EPOCHS = 5
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class AudioDataset(Dataset):
    def __init__(self, root: Path, mfcc_transform):
        self.samples = []
        self.mfcc = mfcc_transform
        for label_dir, label in [("real", 0), ("fake", 1)]:
            for wav in sorted((root / label_dir).glob("*.wav")):
                self.samples.append((str(wav), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        audio, _ = sf.read(path, dtype="float32")
        if len(audio) > MAX_LEN:
            audio = audio[:MAX_LEN]
        else:
            audio = np.pad(audio, (0, MAX_LEN - len(audio)))
        waveform = torch.tensor(audio).unsqueeze(0)  # (1, samples)
        feat = self.mfcc(waveform)  # (1, N_MFCC, time)
        feat = feat.squeeze(0).mean(dim=-1)  # (N_MFCC,) — average over time
        return feat, torch.tensor(label, dtype=torch.long)


class AudioHead(nn.Module):
    """MFCC features + 2-layer classification head."""

    def __init__(self, n_mfcc=N_MFCC, num_labels=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_mfcc, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_labels),
        )

    def forward(self, x):
        return self.net(x)


def train():
    mfcc_transform = MFCC(
        sample_rate=16000, n_mfcc=N_MFCC,
        melkwargs={"n_fft": 512, "hop_length": 160, "n_mels": 64},
    )

    print(f"Loading dataset from {DATA_DIR}...")
    ds = AudioDataset(DATA_DIR, mfcc_transform)
    n = len(ds)
    n_train = int(0.8 * n)
    train_ds, val_ds = torch.utils.data.random_split(
        ds, [n_train, n - n_train],
        generator=torch.Generator().manual_seed(42),
    )
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=BATCH_SIZE)

    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}")

    model = AudioHead().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0
    for epoch in range(EPOCHS):
        model.train()
        correct = total = 0
        for feats, labels in train_dl:
            feats, labels = feats.to(DEVICE), labels.to(DEVICE)
            logits = model(feats)
            loss = criterion(logits, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            correct += (logits.argmax(-1) == labels).sum().item()
            total += len(labels)
        train_acc = correct / total

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for feats, labels in val_dl:
                feats, labels = feats.to(DEVICE), labels.to(DEVICE)
                logits = model(feats)
                correct += (logits.argmax(-1) == labels).sum().item()
                total += len(labels)
        val_acc = correct / total
        print(f"Epoch {epoch+1}/{EPOCHS} — train_acc: {train_acc:.3f}, val_acc: {val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), WEIGHTS_DIR / "head.pt")
            json.dump({
                "n_mfcc": N_MFCC,
                "num_labels": 2,
                "head_layers": [128, 2],
                "feature_extractor": "mfcc",
            }, open(WEIGHTS_DIR / "config.json", "w"))
            print(f"  Saved best weights (val_acc={val_acc:.3f})")

    print(f"Done. Best val_acc: {best_val_acc:.3f}")


if __name__ == "__main__":
    train()
