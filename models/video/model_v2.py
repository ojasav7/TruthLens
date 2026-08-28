"""
Video Deepfake Detector V2 — CNN + Temporal Attention.

Changes from V1:
- Temporal attention instead of vanilla LSTM
- Better frame aggregation
- More robust to variable-length videos

Ponytail: MobileNetV2 backbone is fast on CPU. Attention > LSTM for this task.
"""

import os
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import timm


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "video" / "weights"


class TemporalAttention(nn.Module):
    """Self-attention over frame features."""
    def __init__(self, dim):
        super().__init__()
        self.query = nn.Linear(dim, dim)
        self.key = nn.Linear(dim, dim)
        self.value = nn.Linear(dim, dim)
        self.scale = dim ** 0.5

    def forward(self, x):
        # x: (batch, seq_len, dim)
        q = self.query(x)
        k = self.key(x)
        v = self.value(x)
        attn = torch.bmm(q, k.transpose(1, 2)) / self.scale
        attn = torch.softmax(attn, dim=-1)
        return torch.bmm(attn, v)


class VideoDeepfakeModelV2(nn.Module):
    """CNN + Temporal Attention for video deepfake detection."""

    def __init__(self, num_classes=2, hidden_dim=128):
        super().__init__()
        self.cnn = timm.create_model("mobilenetv2_050", pretrained=True, num_classes=0)
        cnn_out_dim = self.cnn.num_features

        self.temporal_attn = TemporalAttention(cnn_out_dim)
        self.proj = nn.Linear(cnn_out_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        """x: (batch, seq_len, C, H, W)"""
        batch_size, seq_len = x.shape[0], x.shape[1]
        x = x.view(batch_size * seq_len, *x.shape[2:])
        features = self.cnn(x)  # (batch*seq, feat_dim)
        features = features.view(batch_size, seq_len, -1)

        # Temporal attention
        attended = self.temporal_attn(features)  # (batch, seq, feat_dim)

        # Mean pooling over time
        pooled = attended.mean(dim=1)  # (batch, feat_dim)
        pooled = self.proj(pooled)

        return self.classifier(pooled)

    def get_frame_features(self, x):
        """Per-frame CNN features for explainability."""
        batch_size, seq_len = x.shape[0], x.shape[1]
        x = x.view(batch_size * seq_len, *x.shape[2:])
        features = self.cnn(x)
        return features.view(batch_size, seq_len, -1)


class VideoDeepfakeDetectorV2:
    """Video deepfake detector with temporal attention."""

    def __init__(self, weights_path=None, max_frames=10):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR
        self.max_frames = max_frames

        self.model = VideoDeepfakeModelV2(num_classes=2)
        weights_file = self.path / "model_v2.pth"
        if weights_file.exists():
            state_dict = torch.load(weights_file, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print("[Video V2] Loaded trained weights")
        else:
            print(f"[Video V2] No weights, using untrained model")

        self.model.to(self.device)
        self.model.eval()
        self.labels = ["real", "fake"]

        from torchvision import transforms
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _extract_frames(self, video_path, fps=1):
        cap = cv2.VideoCapture(video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(int(video_fps / fps), 1)
        frames = []
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            frame_idx += 1
        cap.release()
        if len(frames) > self.max_frames:
            step = len(frames) / self.max_frames
            frames = [frames[int(i * step)] for i in range(self.max_frames)]
        return frames

    def _transform_frames(self, frames):
        tensors = [self._transform(f) for f in frames]
        return torch.stack(tensors).unsqueeze(0).to(self.device)

    def predict(self, video_path):
        frames = self._extract_frames(video_path)
        if not frames:
            return {"label": "real", "confidence": 0.0, "per_frame_scores": []}

        video_tensor = self._transform_frames(frames)
        with torch.no_grad():
            logits = self.model(video_tensor)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()
            confidence = probs[0, pred_idx].item()

            frame_features = self.model.get_frame_features(video_tensor)
            frame_scores = []
            for i in range(frame_features.shape[1]):
                feat = frame_features[0, i]
                score = torch.sigmoid(feat.mean()).item()
                frame_scores.append({"frame": i, "score": round(score, 4)})

        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
            "per_frame_scores": frame_scores,
        }

    def explain(self, video_path, top_k=5):
        frames = self._extract_frames(video_path)
        if not frames:
            return {"label": "real", "confidence": 0.0, "frame_importance": []}

        video_tensor = self._transform_frames(frames)
        video_tensor.requires_grad_(True)

        logits = self.model(video_tensor)
        probs = torch.softmax(logits, dim=1)
        pred_idx = probs.argmax(dim=1).item()
        confidence = probs[0, pred_idx].item()

        self.model.zero_grad()
        logits[0, pred_idx].backward()

        grads = video_tensor.grad[0]
        frame_importance = grads.flatten(1).norm(dim=1).detach().cpu().numpy()
        if frame_importance.max() > 0:
            frame_importance = frame_importance / frame_importance.max()

        sorted_idx = np.argsort(-frame_importance)[:top_k]
        frame_imp_list = [
            {"frame": int(i), "importance": round(float(frame_importance[i]), 4)}
            for i in sorted_idx
        ]

        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
            "frame_importance": frame_imp_list,
        }
