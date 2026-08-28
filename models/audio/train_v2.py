"""Train Audio V2 — temporal MFCC + attention classification head."""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from torchaudio.transforms import MFCC
import numpy as np
import soundfile as sf
import json

DATA_DIR = Path("data/audio_v2")
WEIGHTS_DIR = Path("models/audio/weights")
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
SR = 16000
MAX_LEN = SR * 2
N_MFCC = 40
TIME_STEPS = 100
BATCH_SIZE = 16
EPOCHS = 8
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class AudioDataset(Dataset):
    def __init__(self, root, mfcc_transform):
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
        waveform = torch.tensor(audio).unsqueeze(0)
        feat = self.mfcc(waveform).squeeze(0)  # (n_mfcc, time)
        # Pad/truncate to fixed time steps
        if feat.shape[1] > TIME_STEPS:
            feat = feat[:, :TIME_STEPS]
        else:
            feat = nn.functional.pad(feat, (0, TIME_STEPS - feat.shape[1]))
        return feat, torch.tensor(label, dtype=torch.long)


def train():
    from models.audio.model_v2 import AudioHeadV2

    mfcc = MFCC(sample_rate=SR, n_mfcc=N_MFCC,
                melkwargs={"n_fft": 512, "hop_length": 160, "n_mels": 64})

    ds = AudioDataset(DATA_DIR, mfcc)
    n = len(ds)
    n_train = int(0.8 * n)
    train_ds, val_ds = torch.utils.data.random_split(
        ds, [n_train, n - n_train], generator=torch.Generator().manual_seed(42))

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=BATCH_SIZE)

    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}")

    model = AudioHeadV2().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
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
        scheduler.step()

        print(f"Epoch {epoch+1}/{EPOCHS} — train_acc: {train_acc:.3f}, val_acc: {val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), WEIGHTS_DIR / "head_v2.pt")
            json.dump({
                "n_mfcc": N_MFCC, "time_steps": TIME_STEPS,
                "num_labels": 2, "head_layers": [128, 64, 2],
                "feature_extractor": "mfcc_temporal",
                "architecture": "attention_pool",
            }, open(WEIGHTS_DIR / "config_v2.json", "w"))
            print(f"  Saved best weights (val_acc={val_acc:.3f})")

    print(f"Done. Best val_acc: {best_val_acc:.3f}")


if __name__ == "__main__":
    train()
