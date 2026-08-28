"""
Image Deepfake Detector V2 — improved classifier head.

Changes from V1:
- Better classifier head with batch norm + dropout
- Grad-CAM explainability preserved
- More robust preprocessing

Ponytail: EfficientNet-B4 backbone is solid. The head was undertrained.
"""

import os
import base64
import io
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import timm
from PIL import Image
from torchvision import transforms

MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "image" / "weights"


class ImageDeepfakeDetectorV2:
    def __init__(self, weights_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR

        # EfficientNet-B4 backbone
        self.backbone = timm.create_model("efficientnet_b4", pretrained=True, num_classes=0)
        feat_dim = self.backbone.num_features

        # Improved classifier head
        self.classifier = nn.Sequential(
            nn.Linear(feat_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 2),
        )

        weights_file = self.path / "model_v2.pth"
        if weights_file.exists():
            state = torch.load(weights_file, map_location=self.device)
            self.backbone.load_state_dict(state["backbone"])
            self.classifier.load_state_dict(state["classifier"])
            print(f"[Image V2] Loaded trained weights")
        else:
            print(f"[Image V2] No weights, using pretrained backbone")

        self.backbone.to(self.device)
        self.classifier.to(self.device)
        self.backbone.eval()
        self.classifier.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self.labels = ["real", "fake"]

    def _load_image(self, image_input):
        if isinstance(image_input, (str, Path)):
            return Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        raise TypeError(f"Unsupported input type: {type(image_input)}")

    def predict(self, image_input):
        img = self._load_image(image_input)
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.backbone(tensor)
            logits = self.classifier(features)
            probs = torch.softmax(logits, dim=-1)
            pred_idx = probs.argmax(dim=-1).item()
            confidence = probs[0][pred_idx].item()

        return {"label": self.labels[pred_idx], "confidence": round(confidence, 4)}

    def explain(self, image_input):
        """Grad-CAM heatmap via backbone features."""
        img = self._load_image(image_input)
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        # Use the last conv layer of EfficientNet
        target_layer = self.backbone.conv_head

        activations = []
        gradients = []

        def fwd_hook(module, input, output):
            activations.append(output.detach())

        def bwd_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0].detach())

        h1 = target_layer.register_forward_hook(fwd_hook)
        h2 = target_layer.register_full_backward_hook(bwd_hook)

        self.backbone.zero_grad()
        self.classifier.zero_grad()
        features = self.backbone(tensor)
        logits = self.classifier(features)
        pred_idx = logits.argmax(dim=-1).item()
        logits[0, pred_idx].backward()

        act = activations[0].squeeze(0)
        grad = gradients[0].squeeze(0)
        weights = grad.mean(dim=(1, 2))

        cam = torch.zeros(act.shape[1:], device=act.device)
        for i, w in enumerate(weights):
            cam += w * act[i]
        cam = torch.relu(cam)
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        cam_np = cam.cpu().numpy()
        cam_resized = cv2.resize(cam_np, (224, 224))
        cam_uint8 = np.uint8(cam_resized * 255)
        heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        img_resized = np.array(img.resize((224, 224)))
        overlay = np.uint8(img_resized * 0.5 + heatmap * 0.5)

        overlay_pil = Image.fromarray(overlay)
        buf = io.BytesIO()
        overlay_pil.save(buf, format="PNG")
        heatmap_b64 = base64.b64encode(buf.getvalue()).decode()

        h1.remove()
        h2.remove()

        confidence = torch.softmax(logits, dim=-1)[0, pred_idx].item()
        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
            "explained_output": "logits",
            "class_index": pred_idx,
            "class_name": self.labels[pred_idx],
            "heatmap_b64": heatmap_b64,
        }
