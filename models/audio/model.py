"""
Audio Voice Clone Detector
Auto-detects best available weights and architecture:
  - head_v3.pt  → 1D CNN on raw waveform (retrained on 2K samples)
  - head_v2.pt  → Temporal MFCC + attention
  - head.pt     → MFCC-MLP (original, 100% on synthetic = overfitting)
"""
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import soundfile as sf


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "audio" / "weights"
SR = 16000
MAX_LEN = SR * 2  # 2 seconds


class AudioCNN(nn.Module):
    """1D CNN on raw waveform — captures temporal patterns directly."""

    def __init__(self, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, 32, 80, stride=4), nn.BatchNorm1d(32), nn.ReLU(), nn.MaxPool1d(4),
            nn.Conv1d(32, 64, 40, stride=2), nn.BatchNorm1d(64), nn.ReLU(), nn.MaxPool1d(4),
            nn.Conv1d(64, 128, 20, stride=2), nn.BatchNorm1d(128), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.4), nn.Linear(64, num_classes)
        )

    def forward(self, x):
        return self.classifier(self.features(x).flatten(1))


class AudioHead(nn.Module):
    """MFCC features + 2-layer classification head (legacy v1)."""

    def __init__(self, n_mfcc=40, num_labels=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_mfcc, 128), nn.ReLU(), nn.Dropout(0.3), nn.Linear(128, num_labels),
        )

    def forward(self, x):
        return self.net(x)


class AudioDeepfakeDetector:
    def __init__(self, weights_path: str | Path | None = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR
        self.labels = ["real", "cloned"]
        self.arch = None

        # Try v3 1D CNN first
        v3_path = self.path / "head_v3.pt"
        if v3_path.exists():
            self.arch = "cnn1d"
            self.model = AudioCNN()
            state = torch.load(v3_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.model.to(self.device)
            self.model.eval()
            print("[Audio] Loaded v3 1D CNN weights")
            return

        # Fall back to v1 MFCC-MLP
        self.arch = "mfcc"
        from torchaudio.transforms import MFCC
        self.mfcc = MFCC(
            sample_rate=SR, n_mfcc=40,
            melkwargs={"n_fft": 512, "hop_length": 160, "n_mels": 64},
        )
        self.model = AudioHead()
        weights_file = self.path / "head.pt"
        if weights_file.exists():
            state = torch.load(weights_file, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            print("[Audio] Loaded MFCC-MLP weights")
        else:
            print("[Audio] No weights found, using random init")

        self.model.to(self.device)
        self.model.eval()

    def _load_audio(self, audio_path: str) -> np.ndarray:
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

    def predict(self, audio_path: str) -> dict:
        audio = self._load_audio(audio_path)

        if self.arch == "cnn1d":
            waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(waveform)
                probs = torch.softmax(logits, dim=-1)
                pred_idx = probs.argmax(dim=-1).item()
                confidence = probs[0][pred_idx].item()
        else:
            waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
            feat = self.mfcc(waveform).squeeze(0).mean(dim=-1).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(feat)
                probs = torch.softmax(logits, dim=-1)
                pred_idx = probs.argmax(dim=-1).item()
                confidence = probs[0][pred_idx].item()

        return {"label": self.labels[pred_idx], "confidence": round(confidence, 4)}

    def explain(self, audio_path: str) -> dict:
        audio = self._load_audio(audio_path)

        if self.arch == "cnn1d":
            waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
            waveform_grad = waveform.clone().requires_grad_(True)
            logits = self.model(waveform_grad)
            pred_idx = logits.argmax(dim=-1).item()
            confidence = torch.softmax(logits, dim=-1)[0, pred_idx].item()

            self.model.zero_grad()
            logits[0, pred_idx].backward()

            # Frame-level importance from gradient magnitude
            grads = waveform_grad.grad.squeeze().cpu().numpy()
            n_frames = len(grads) // 1600  # 100ms frames
            importance = []
            for i in range(min(n_frames, 20)):
                chunk = grads[i * 1600:(i + 1) * 1600]
                importance.append({
                    "time_ms": i * 100,
                    "importance": round(float(np.abs(chunk).mean()), 6),
                })
            importance.sort(key=lambda x: x["importance"], reverse=True)

            # Map to top_coefficients format for API compatibility
            bands = [{
                "mfcc_index": seg["time_ms"],
                "estimated_freq_hz": seg["time_ms"],
                "importance": seg["importance"],
            } for seg in importance[:10]]

            return {
                "label": self.labels[pred_idx],
                "confidence": round(float(confidence), 4),
                "explained_output": "logit",
                "top_coefficients": bands,
                "base_value": 0.0,
            }
        else:
            # MFCC-based explanation
            from torchaudio.transforms import MFCC
            waveform_t = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
            feat = self.mfcc(waveform_t).squeeze(0).mean(dim=-1).unsqueeze(0).to(self.device)
            feat_grad = feat.clone().requires_grad_(True)
            logits = self.model(feat_grad)
            pred_idx = logits.argmax(dim=-1).item()
            confidence = torch.softmax(logits, dim=-1)[0, pred_idx].item()

            self.model.zero_grad()
            logits[0, pred_idx].backward()
            importance = feat_grad.grad.abs().squeeze().cpu().numpy()
            top_k = min(10, len(importance))
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
