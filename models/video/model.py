"""
Video Deepfake Detector — Phase 3
CNN backbone (EfficientNet) + LSTM temporal model for video deepfake detection.
"""

import os
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import timm


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "video" / "weights"


class VideoDeepfakeDetector:
    """Video deepfake classifier: extracts frames, runs CNN+LSTM, aggregates scores."""

    def __init__(self, weights_path: str | Path | None = None, max_frames: int = 10):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR
        self.max_frames = max_frames

        # Try hidden_dim=64 first (retrained model), fall back to 128 (original)
        self.model = VideoDeepfakeModel(num_classes=2, hidden_dim=64)

        weights_file = self.path / "model.pth"
        if weights_file.exists():
            state_dict = torch.load(weights_file, map_location=self.device, weights_only=True)
            try:
                self.model.load_state_dict(state_dict)
                print("Loaded trained video weights (hidden=64)")
            except RuntimeError:
                # Fall back to original architecture
                self.model = VideoDeepfakeModel(num_classes=2, hidden_dim=128)
                self.model.load_state_dict(state_dict)
                print("Loaded trained video weights (hidden=128)")
        else:
            print(f"No weights at {weights_file}, using untrained model")

        self.model.to(self.device)
        self.model.eval()
        self.labels = ["real", "fake"]

        # Cache transforms
        from torchvision import transforms
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _extract_frames(self, video_path: str, fps: int = 1) -> list:
        """Extract frames from video at specified FPS using OpenCV."""
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

        # Uniformly sample max_frames
        if len(frames) > self.max_frames:
            step = len(frames) / self.max_frames
            frames = [frames[int(i * step)] for i in range(self.max_frames)]

        return frames

    def _transform_frames(self, frames: list) -> torch.Tensor:
        """Convert list of RGB frames to normalized tensor."""
        tensors = [self._transform(f) for f in frames]
        return torch.stack(tensors).unsqueeze(0).to(self.device)

    def predict(self, video_path: str) -> dict:
        """Classify a video as real or fake using CNN+LSTM model."""
        frames = self._extract_frames(video_path)
        if not frames:
            return {"label": "real", "confidence": 0.0, "per_frame_scores": []}

        video_tensor = self._transform_frames(frames)

        with torch.no_grad():
            logits = self.model(video_tensor)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()
            confidence = probs[0, pred_idx].item()

            # Per-frame scores via CNN features
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

    def explain(self, video_path: str, top_k: int = 5) -> dict:
        """Temporal explainability: which frames contribute most to the prediction.
        Uses gradient-based frame importance via LSTM hidden states."""
        frames = self._extract_frames(video_path)
        if not frames:
            return {"label": "real", "confidence": 0.0, "frame_importance": []}

        video_tensor = self._transform_frames(frames)
        video_tensor.requires_grad_(True)

        # Forward pass with gradient tracking
        logits = self.model(video_tensor)
        probs = torch.softmax(logits, dim=1)
        pred_idx = probs.argmax(dim=1).item()
        confidence = probs[0, pred_idx].item()

        # Backprop from predicted class to input frames
        self.model.zero_grad()
        logits[0, pred_idx].backward()

        # Frame importance = L2 norm of input gradient per frame
        grads = video_tensor.grad[0]  # (seq_len, C, H, W)
        frame_importance = grads.flatten(1).norm(dim=1).detach().cpu().numpy()

        # Normalize to [0, 1]
        if frame_importance.max() > 0:
            frame_importance = frame_importance / frame_importance.max()

        # Sort by importance
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


class VideoDeepfakeModel(nn.Module):
    """CNN + LSTM architecture for video deepfake detection.
    Uses MobileNetV2 for fast CPU training/inference."""

    def __init__(self, num_classes: int = 2, hidden_dim: int = 128):
        super().__init__()
        self.cnn = timm.create_model("mobilenetv2_050", pretrained=True, num_classes=0)
        cnn_out_dim = self.cnn.num_features
        self.lstm = nn.LSTM(cnn_out_dim, hidden_dim, batch_first=True, num_layers=1)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        """
        Args:
            x: tensor of shape (batch, seq_len, C, H, W)
        Returns:
            logits: (batch, num_classes)
        """
        batch_size, seq_len = x.shape[0], x.shape[1]
        x = x.view(batch_size * seq_len, *x.shape[2:])
        features = self.cnn(x)
        features = features.view(batch_size, seq_len, -1)
        lstm_out, _ = self.lstm(features)
        last_hidden = lstm_out[:, -1, :]
        logits = self.classifier(last_hidden)
        return logits

    def get_frame_features(self, x):
        """Extract per-frame CNN features for temporal explainability."""
        batch_size, seq_len = x.shape[0], x.shape[1]
        x = x.view(batch_size * seq_len, *x.shape[2:])
        features = self.cnn(x)
        return features.view(batch_size, seq_len, -1)
