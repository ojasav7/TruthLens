"""
Image Deepfake Classifier -- Phase 2
EfficientNet-B4 + Grad-CAM explainability.
"""

import os
import base64
import io
from pathlib import Path

import cv2
import numpy as np
import torch
import timm
from PIL import Image
from torchvision import transforms


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "image" / "weights"


class ImageDeepfakeDetector:
    def __init__(self, weights_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR

        self.model = timm.create_model("efficientnet_b4", pretrained=True, num_classes=2)
        weights_file = self.path / "model.pth"
        if weights_file.exists():
            self.model.load_state_dict(
                torch.load(weights_file, map_location=self.device)
            )
        else:
            print(f"[Warning] No weights at {weights_file}, using ImageNet-pretrained head")

        self.model.to(self.device)
        self.model.eval()

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

    def predict(self, image_input) -> dict:
        img = self._load_image(image_input)
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=-1)
            pred_idx = probs.argmax(dim=-1).item()
            confidence = probs[0][pred_idx].item()

        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
        }

    def explain(self, image_input) -> dict:
        """Predict with Grad-CAM heatmap showing which regions drive the classification."""
        img = self._load_image(image_input)
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        # timm EfficientNet: last conv is conv_head
        target_layer = self.model.conv_head

        # Hook to capture gradients and activations
        activations = []
        gradients = []

        def forward_hook(module, input, output):
            activations.append(output.detach())

        def backward_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0].detach())

        handle_fwd = target_layer.register_forward_hook(forward_hook)
        handle_bwd = target_layer.register_full_backward_hook(backward_hook)

        # Forward + backward for predicted class
        self.model.zero_grad()
        logits = self.model(tensor)
        pred_idx = logits.argmax(dim=-1).item()
        logits[0, pred_idx].backward()

        # Compute Grad-CAM
        act = activations[0].squeeze(0)  # (C, H, W)
        grad = gradients[0].squeeze(0)   # (C, H, W)
        weights = grad.mean(dim=(1, 2))  # (C,)

        cam = torch.zeros(act.shape[1:], device=act.device)
        for i, w in enumerate(weights):
            cam += w * act[i]
        cam = torch.relu(cam)

        # Normalize to 0-1
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        # Resize to original image size
        cam_np = cam.cpu().numpy()
        cam_resized = cv2.resize(cam_np, (224, 224))

        # Create heatmap overlay
        cam_uint8 = np.uint8(cam_resized * 255)
        heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        # Overlay on original image
        img_resized = np.array(img.resize((224, 224)))
        overlay = np.uint8(img_resized * 0.5 + heatmap * 0.5)

        # Encode as base64 PNG
        overlay_pil = Image.fromarray(overlay)
        buf = io.BytesIO()
        overlay_pil.save(buf, format="PNG")
        heatmap_b64 = base64.b64encode(buf.getvalue()).decode()

        handle_fwd.remove()
        handle_bwd.remove()

        confidence = torch.softmax(logits, dim=-1)[0, pred_idx].item()
        return {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
            "explained_output": "logits",
            "class_index": pred_idx,
            "class_name": self.labels[pred_idx],
            "heatmap_b64": heatmap_b64,
        }
