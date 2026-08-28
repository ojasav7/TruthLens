"""
Image Deepfake Classifier
Auto-detects best available weights and architecture:
  - model_v3.pth → SimpleCNN at 64x64 (fastest, retrained on 6K images)
  - model.pth    → EfficientNet-B4 at 224x224 (original, 59% accuracy)
"""
import os, base64, io
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms


MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models")) / "image" / "weights"


class ImageCNN(nn.Module):
    """Lightweight CNN — trains fast, good accuracy on 6K+ images."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.4), nn.Linear(64, 2)
        )

    def forward(self, x):
        return self.classifier(self.features(x).flatten(1))


class ImageDeepfakeDetector:
    def __init__(self, weights_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.path = Path(weights_path) if weights_path else MODEL_DIR
        self.labels = ["real", "fake"]
        self.arch = None  # "cnn" or "efficientnet"

        # Try realistic weights first (trained on realistic synthetic data)
        realistic_path = self.path / "model_realistic.pth"
        if realistic_path.exists():
            self.arch = "cnn"
            self.model = ImageCNN()
            state = torch.load(realistic_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.model.to(self.device)
            self.model.eval()
            self.labels = ["real", "fake"]
            self.transform = transforms.Compose([
                transforms.Resize((64, 64)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
            print("[Image] Loaded realistic CNN weights (64x64)")
            return

        # Try v3 weights (fast CNN)
        v3_path = self.path / "model_v3.pth"
        if v3_path.exists():
            self.arch = "cnn"
            self.model = ImageCNN()
            state = torch.load(v3_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.model.to(self.device)
            self.model.eval()
            # ImageFolder uses alphabetical class order: fake=0, real=1
            self.labels = ["fake", "real"]
            self.transform = transforms.Compose([
                transforms.Resize((64, 64)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
            print("[Image] Loaded v3 CNN weights (64x64)")
            return

        # Fall back to EfficientNet
        import timm
        self.arch = "efficientnet"
        self.model = timm.create_model("efficientnet_b4", pretrained=True, num_classes=2)
        weights_file = self.path / "model.pth"
        if weights_file.exists():
            self.model.load_state_dict(
                torch.load(weights_file, map_location=self.device, weights_only=True)
            )
            print("[Image] Loaded EfficientNet weights")
        else:
            print("[Image] No weights found, using ImageNet-pretrained head")

        self.model.to(self.device)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def _load_image(self, image_input):
        if isinstance(image_input, (str, Path)):
            return Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        raise TypeError(f"Unsupported input type: {type(image_input)}")

    def _is_real_photo(self, img: Image.Image) -> bool:
        """Detect if an image is a real photograph vs synthetic/generated.

        Real photos have: high texture complexity, natural color variance,
        proper exposure, and non-uniform pixel distribution.
        Synthetic training data (our v3) is flat geometric patterns.
        """
        arr = np.array(img)

        # 1. Texture complexity via Laplacian variance
        # Real photos have rich textures (skin, hair, fabric); flat patterns don't
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 200:  # Very flat = synthetic
            return False

        # 2. Color channel variance — real photos have diverse colors
        channel_stds = [arr[:, :, c].std() for c in range(3)]
        avg_std = np.mean(channel_stds)
        if avg_std < 25:  # Very uniform colors = synthetic
            return False

        # 3. Resolution — real photos are typically > 200px on each side
        w, h = img.size
        if w < 100 or h < 100:  # Tiny images are likely synthetic
            return False

        # 4. Pixel histogram spread — real photos use full 0-255 range
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        nonzero = np.count_nonzero(hist > hist.max() * 0.001)
        if nonzero < 50:  # Narrow histogram = synthetic
            return False

        # 5. JPEG compression artifacts — real photos from cameras have them
        # Check if image has natural noise patterns
        noise = gray.astype(np.float64)
        noise_diff = np.abs(noise[:, 1:].astype(np.float64) - noise[:, :-1].astype(np.float64))
        noise_mean = noise_diff.mean()
        # Real photos have subtle sensor noise; synthetic patterns are too clean or too noisy
        if noise_mean < 1.0 or noise_mean > 30:  # Too clean or too noisy
            return False

        return True

    def predict(self, image_input) -> dict:
        img = self._load_image(image_input)

        # Use ensemble detector for multi-signal analysis
        from models.image.ensemble import ensemble_predict
        result = ensemble_predict(img, cnn_model=self)

        # Add CNN-specific details
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=-1)
            pred_idx = probs.argmax(dim=-1).item()
            confidence = probs[0][pred_idx].item()

        result["cnn_raw"] = {
            "label": self.labels[pred_idx],
            "confidence": round(confidence, 4),
        }

        return result

    def explain(self, image_input) -> dict:
        img = self._load_image(image_input)
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        # Use Grad-CAM on last conv layer
        if self.arch == "efficientnet":
            target_layer = self.model.conv_head
        else:
            # For CNN: use last conv in features
            target_layer = self.model.features[-4]  # Conv2d(64,128)

        activations = []
        gradients = []

        def fwd_hook(module, input, output):
            activations.append(output.detach())
        def bwd_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0].detach())

        h1 = target_layer.register_forward_hook(fwd_hook)
        h2 = target_layer.register_full_backward_hook(bwd_hook)

        self.model.zero_grad()
        logits = self.model(tensor)
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
        img_size = 64 if self.arch == "cnn" else 224
        cam_resized = cv2.resize(cam_np, (img_size, img_size))
        cam_uint8 = np.uint8(cam_resized * 255)
        heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        img_resized = np.array(img.resize((img_size, img_size)))
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
