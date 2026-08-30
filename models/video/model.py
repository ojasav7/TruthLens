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
                print("[Video] Loaded trained video weights (hidden=64)")
            except RuntimeError:
                # Fall back to original architecture
                self.model = VideoDeepfakeModel(num_classes=2, hidden_dim=128)
                self.model.load_state_dict(state_dict)
                print("[Video] Loaded trained video weights (hidden=128)")
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

    def _is_real_video(self, frames: list) -> bool:
        """Detect if a video contains real-world footage vs synthetic patterns.

        Real videos have: high texture complexity, natural color diversity,
        proper resolution, and temporal consistency.
        Synthetic training data is 64x64 sine wave patterns.
        """
        if not frames:
            return False

        # Check resolution — real videos are typically >100px
        h, w = frames[0].shape[:2]
        if w < 100 or h < 100:
            return False

        # Check texture complexity across multiple frames
        import cv2
        lap_vars = []
        color_stds = []
        for frame in frames[:5]:  # Sample first 5 frames
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            lap_vars.append(cv2.Laplacian(gray, cv2.CV_64F).var())
            color_stds.append(np.mean([frame[:, :, c].std() for c in range(3)]))

        avg_lap = np.mean(lap_vars)
        avg_std = np.mean(color_stds)

        # Real videos have complex textures (laplacian > 50 for compressed video)
        if avg_lap < 50:
            return False

        # Real videos have diverse colors (std > 20)
        if avg_std < 20:
            return False

        # Check temporal consistency — real videos don't change radically between frames
        diffs = []
        for i in range(1, min(5, len(frames))):
            diff = np.abs(frames[i].astype(float) - frames[i-1].astype(float)).mean()
            diffs.append(diff)
        avg_diff = np.mean(diffs) if diffs else 0

        # Real videos have smooth motion (diff < 50); synthetic random noise has high diff
        if avg_diff > 50:
            return False

        return True

    def predict(self, video_path: str) -> dict:
        """Classify a video as real or fake using multi-signal ensemble."""
        frames = self._extract_frames(video_path)
        if not frames:
            return {"label": "real", "confidence": 0.0, "per_frame_scores": []}

        # --- Multi-signal ensemble ---
        signals = {}

        # Signal 1: Resolution check
        h, w = frames[0].shape[:2]
        signals["resolution"] = f"{w}x{h}"
        signals["is_low_res"] = w < 100 or h < 100

        # Signal 2: Realism heuristic (texture, color, temporal consistency)
        is_real = self._is_real_video(frames)
        signals["is_real_footage"] = is_real

        # Signal 3: CNN+LSTM model prediction
        video_tensor = self._transform_frames(frames)
        with torch.no_grad():
            logits = self.model(video_tensor)
            probs = torch.softmax(logits, dim=1)
            pred_idx = probs.argmax(dim=1).item()
            confidence = probs[0, pred_idx].item()

            # Per-frame scores
            frame_features = self.model.get_frame_features(video_tensor)
            frame_scores = []
            for i in range(frame_features.shape[1]):
                feat = frame_features[0, i]
                score = torch.sigmoid(feat.mean()).item()
                frame_scores.append({"frame": i, "score": round(score, 4)})

        model_label = self.labels[pred_idx]
        signals["model"] = {"label": model_label, "confidence": round(confidence, 4)}

        # Signal 4: Frame-to-frame consistency
        diffs = []
        for i in range(1, min(len(frames), 10)):
            diff = np.abs(frames[i].astype(float) - frames[i-1].astype(float)).mean()
            diffs.append(diff)
        avg_diff = np.mean(diffs) if diffs else 0
        signals["temporal_diff"] = round(avg_diff, 2)

        # Signal 5: FFT frequency analysis (deepfakes have more high-freq artifacts)
        fft_scores = []
        for frame in frames[:5]:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude = np.log(np.abs(f_shift) + 1)
            fh, fw = magnitude.shape
            center_h, center_w = fh // 2, fw // 2
            radius = min(fh, fw) // 4
            total_energy = magnitude.sum()
            low_energy = magnitude[center_h-radius:center_h+radius, center_w-radius:center_w+radius].sum()
            hf_ratio = 1.0 - (low_energy / (total_energy + 1e-10))
            fft_scores.append(hf_ratio)
        signals["fft_hf_ratio"] = round(float(np.mean(fft_scores)), 4)

        # Signal 6: Compression artifacts (block boundary analysis)
        block_scores = []
        for frame in frames[:3]:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(float)
            fh_b, fw_b = gray.shape
            if fh_b >= 16 and fw_b >= 16:
                v_diff = np.abs(gray[8::8, :] - np.roll(gray[8::8, :], 1, axis=1)).mean()
                h_diff = np.abs(gray[:, 8::8] - np.roll(gray[:, 8::8], 1, axis=0)).mean()
                block_scores.append((v_diff + h_diff) / 2)
        signals["compression_artifacts"] = round(float(np.mean(block_scores)) if block_scores else 0, 4)

        # Signal 7: Color channel correlation
        channel_corrs = []
        for frame in frames[:5]:
            r, g, b = frame[:,:,0].astype(float), frame[:,:,1].astype(float), frame[:,:,2].astype(float)
            rg_corr = np.corrcoef(r.flatten(), g.flatten())[0, 1]
            rb_corr = np.corrcoef(r.flatten(), b.flatten())[0, 1]
            gb_corr = np.corrcoef(g.flatten(), b.flatten())[0, 1]
            channel_corrs.append(abs(rg_corr) + abs(rb_corr) + abs(gb_corr))
        signals["channel_correlation"] = round(float(np.mean(channel_corrs)), 4)

        # --- Decision logic ---
        # For compressed video (FF++ c23), signal-level analysis is unreliable.
        # Use the trained CNN+LSTM model as primary signal, with signal checks
        # for obvious synthetic content (very low resolution, no faces, etc.)

        # Build explanation
        vote_details = []
        vote_details.append(f"Model: {model_label} ({confidence:.1%})")
        vote_details.append(f"Temporal: {avg_diff:.1f}")
        vote_details.append(f"FFT HF: {signals['fft_hf_ratio']:.3f}")
        vote_details.append(f"Compression: {signals['compression_artifacts']:.1f}")
        vote_details.append(f"Channel corr: {signals['channel_correlation']:.2f}")

        # Check for obviously synthetic content
        is_obviously_synthetic = (
            signals["is_low_res"] and
            signals["fft_hf_ratio"] > 0.8 and
            avg_diff > 50
        )
        is_obviously_real = (
            not signals["is_low_res"] and
            signals["compression_artifacts"] > 3 and
            signals["channel_correlation"] > 4.0
        )

        if is_obviously_synthetic:
            label = "fake"
            conf = 0.85
        elif is_obviously_real:
            label = "real"
            conf = 0.80
        elif model_label == "fake" and confidence > 0.6:
            label = "fake"
            conf = confidence
        elif model_label == "real" and confidence > 0.6:
            label = "real"
            conf = confidence
        else:
            label = "indeterminate"
            conf = confidence

        return {
            "label": label,
            "confidence": round(conf, 4),
            "per_frame_scores": frame_scores,
            "signals": signals,
            "verdict": f"Video analysis: {label.upper()} ({conf:.1%}). {' | '.join(vote_details)}",
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
