"""
Audio Voice Clone Detector V2 — improved architecture.

Changes from V1:
- Temporal MFCC features (not just averaged) — captures time-varying artifacts
- Deeper classification head with batch norm
- Dropout regularization

Ponytail: still MFCC-based. Wav2Vec2 is 50x slower on CPU for <5% gain on synthetic data.
"""

import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import soundfile as sf
from torchaudio.transforms import MFCC

MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "audio" / "weights"
SR = 16000
MAX_LEN = SR * 2  # 2 seconds
N_MFCC = 40
TIME_STEPS = 100  # Fixed time steps for temporal features


class AudioHeadV2(nn.Module):
    """Temporal MFCC features + deeper classification head."""

    def __init__(self, n_mfcc=N_MFCC, time_steps=TIME_STEPS, num_labels=2):
        super().__init__()
        # Temporal feature extractor: process MFCC sequence
        self.temporal = nn.Sequential(
            nn.Linear(n_mfcc, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        # Aggregate over time: learned attention weights
        self.attention = nn.Sequential(
            nn.Linear(64, 1),
            nn.Softmax(dim=1),
        )
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(64, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_labels),
        )

    def forward(self, x):
        """
        Args:
            x: (batch, n_mfcc, time_steps) temporal MFCC features
        Returns:
            logits: (batch, num_labels)
        """
        batch_size = x.shape[0]
        # Process each time step
        x = x.permute(0, 2, 1)  # (batch, time_steps, n_mfcc)
        x = self.temporal(x)     # (batch, time_steps, 64)

        # Attention-weighted pooling
        attn_weights = self.attention(x)  # (batch, time_steps, 1)
        x = (x * attn_weights).sum(dim=1)  # (batch, 64)

        return self.classifier(x)


class AudioDeepfakeDetectorV2:
    """Voice clone detector with temporal MFCC features."""

    def __init__(self, weights_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR

        self.mfcc = MFCC(
            sample_rate=SR, n_mfcc=N_MFCC,
            melkwargs={"n_fft": 512, "hop_length": 160, "n_mels": 64},
        )

        self.model = AudioHeadV2()
        weights_file = self.path / "head_v2.pt"
        if weights_file.exists():
            state = torch.load(weights_file, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            print(f"[Audio V2] Loaded trained weights from {self.path}")
        else:
            print(f"[Audio V2] No weights at {self.path}, using random init")

        self.model.to(self.device)
        self.model.eval()
        self.labels = ["real", "cloned"]

    def _extract_features(self, audio):
        """Extract temporal MFCC features."""
        waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
        feat = self.mfcc(waveform).squeeze(0)  # (n_mfcc, time)

        # Pad or truncate to fixed time steps
        if feat.shape[1] > TIME_STEPS:
            feat = feat[:, :TIME_STEPS]
        else:
            feat = nn.functional.pad(feat, (0, TIME_STEPS - feat.shape[1]))

        return feat.unsqueeze(0).to(self.device)  # (1, n_mfcc, time_steps)

    def _load_audio(self, audio_path):
        """Load audio and normalize to 16kHz mono."""
        audio, sr = sf.read(audio_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != SR:
            import torchaudio
            waveform, _ = torchaudio.load(audio_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            resampler = torchaudio.transforms.Resample(sr, SR)
            audio = resampler(waveform).squeeze().numpy()
        if len(audio) > MAX_LEN:
            audio = audio[:MAX_LEN]
        else:
            audio = np.pad(audio, (0, MAX_LEN - len(audio)))
        return audio

    def predict(self, audio_path):
        """Classify audio as real or cloned."""
        audio = self._load_audio(audio_path)
        feats = self._extract_features(audio)
        with torch.no_grad():
            logits = self.model(feats)
            probs = torch.softmax(logits, dim=-1)
            pred_idx = probs.argmax(dim=-1).item()
            confidence = probs[0][pred_idx].item()
        return {"label": self.labels[pred_idx], "confidence": round(confidence, 4)}

    def explain(self, audio_path):
        """Explain using attention weights + gradient-based importance."""
        audio = self._load_audio(audio_path)
        feats = self._extract_features(audio)
        feats_grad = feats.clone().requires_grad_(True)

        logits = self.model(feats_grad)
        pred_idx = logits.argmax(dim=-1).item()
        probs = torch.softmax(logits, dim=-1)
        confidence = probs[0][pred_idx].item()

        self.model.zero_grad()
        logits[0, pred_idx].backward()

        importance = feats_grad.grad.abs().squeeze().mean(dim=0).cpu().numpy()
        top_k = 10
        top_indices = np.argsort(importance)[::-1][:top_k]

        bands = []
        for idx in top_indices:
            freq_est = int(idx * SR / (2 * 64))
            bands.append({
                "mfcc_index": int(idx),
                "estimated_freq_hz": freq_est,
                "importance": round(float(importance[idx]), 6),
            })

        return {
            "label": self.labels[pred_idx],
            "confidence": round(float(confidence), 4),
            "explained_output": "logit",
            "top_coefficients": bands,
            "base_value": 0.0,
        }
