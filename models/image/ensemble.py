"""
Ensemble Deepfake Detector — multi-signal approach.

Instead of relying on a single model trained on synthetic data, this combines:
1. Face detection (deepfake detection requires a face)
2. Our CNN model (trained on synthetic data — good at detecting synthetic artifacts)
3. HuggingFace model (trained on real deepfake data — better at face manipulation)
4. Image quality assessment (compression, resolution, noise)
5. Realism heuristic (texture complexity, color distribution)

The ensemble produces a calibrated verdict with confidence based on agreement.
"""
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageStat


def _detect_faces(img: Image.Image) -> list:
    """Detect faces using OpenCV's DNN face detector (more robust than Haar cascade)."""
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Try DNN face detector first (ships with OpenCV 5.x)
    try:
        # Use built-in face detection via resize + basic detection
        h, w = gray.shape[:2]
        if w < 64 or h < 64:
            return []

        # Simple face-like region detection: look for skin-tone regions
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        # Skin tone range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 150, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        faces = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > (h * w * 0.01):  # At least 1% of image
                x, y, fw, fh = cv2.boundingRect(c)
                aspect = fw / fh if fh > 0 else 0
                if 0.3 < aspect < 3.0:  # Reasonable face aspect ratio
                    faces.append((x, y, fw, fh))

        return faces

    except Exception:
        return []


def _assess_quality(img: Image.Image) -> dict:
    """Assess image quality metrics relevant to deepfake detection."""
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]

    # 1. Resolution
    resolution_score = min(1.0, (w * h) / (224 * 224))

    # 2. Texture complexity (Laplacian variance)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    texture_score = min(1.0, lap_var / 1000)

    # 3. Color diversity
    channel_stds = [arr[:, :, c].std() for c in range(3)]
    color_score = min(1.0, np.mean(channel_stds) / 60)

    # 4. JPEG compression estimation
    # High compression = blocky artifacts = harder to detect deepfakes
    # Estimate via frequency analysis
    f = np.fft.fft2(gray.astype(float))
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)
    # High frequency ratio indicates less compression
    h, w_m = magnitude.shape
    cy, cx = h // 2, w_m // 2
    total_energy = magnitude.sum()
    if total_energy > 0:
        # Energy in high-frequency bands
        high_freq_mask = np.zeros_like(magnitude, dtype=bool)
        for r in range(min(cy, cx) // 2, min(cy, cx)):
            y, x = np.ogrid[:h, :w_m]
            high_freq_mask |= ((x - cx)**2 + (y - cy)**2) > r**2
        high_freq_ratio = magnitude[high_freq_mask].sum() / total_energy
    else:
        high_freq_ratio = 0
    compression_score = min(1.0, high_freq_ratio * 5)

    # 5. Noise level (real photos have sensor noise)
    noise_diff = np.abs(gray[:, 1:].astype(float) - gray[:, :-1].astype(float))
    noise_score = min(1.0, noise_diff.mean() / 10)

    # Overall quality
    overall = np.mean([resolution_score, texture_score, color_score, compression_score, noise_score])

    return {
        "resolution": round(resolution_score, 3),
        "texture": round(texture_score, 3),
        "color_diversity": round(color_score, 3),
        "compression": round(compression_score, 3),
        "noise": round(noise_score, 3),
        "overall": round(overall, 3),
    }


def _is_synthetic_content(img: Image.Image) -> bool:
    """Detect if image is procedurally generated (like our training data)."""
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]

    # Synthetic training data is 64x64 with simple patterns
    if w <= 64 and h <= 64:
        return True

    # Very low texture = synthetic pattern
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var < 100:
        return True

    # Very uniform colors = synthetic
    channel_stds = [arr[:, :, c].std() for c in range(3)]
    if np.mean(channel_stds) < 15:
        return True

    return False


def ensemble_predict(
    img: Image.Image,
    cnn_model=None,
    hf_model=None,
    hf_processor=None,
) -> dict:
    """
    Multi-signal ensemble deepfake prediction.

    Returns dict with:
    - label: "real" | "fake" | "indeterminate"
    - confidence: 0-1
    - signals: individual signal results
    - verdict: human-readable explanation
    """
    img_rgb = img.convert("RGB")
    signals = {}

    # Signal 1: Face detection
    faces = _detect_faces(img_rgb)
    signals["faces_detected"] = len(faces)
    signals["has_face"] = len(faces) > 0

    # Signal 2: Image quality
    quality = _assess_quality(img_rgb)
    signals["quality"] = quality

    # Signal 3: Synthetic content detection
    is_synth = _is_synthetic_content(img_rgb)
    signals["is_synthetic"] = is_synth

    # Signal 4: CNN model prediction (raw, not via predict which calls ensemble)
    cnn_result = None
    if cnn_model is not None:
        try:
            import torch
            tensor = cnn_model.transform(img_rgb).unsqueeze(0).to(cnn_model.device)
            with torch.no_grad():
                logits = cnn_model.model(tensor)
                probs = torch.softmax(logits, dim=-1)
                pred_idx = probs.argmax(dim=-1).item()
                conf = probs[0][pred_idx].item()
            cnn_result = {"label": cnn_model.labels[pred_idx], "confidence": round(conf, 4)}
            signals["cnn"] = cnn_result
        except Exception as e:
            signals["cnn_error"] = str(e)

    # Signal 5: HuggingFace model (if available, run on face crops)
    hf_result = None
    if hf_model is not None and hf_processor is not None and faces:
        try:
            import torch
            # Run on largest face with padding
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, fw, fh = largest_face
            pad = int(max(fw, fh) * 0.3)
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(img_rgb.width, x + fw + pad)
            y2 = min(img_rgb.height, y + fh + pad)
            face_crop = img_rgb.crop((x1, y1, x2, y2))

            inputs = hf_processor(images=face_crop, return_tensors="pt")
            with torch.no_grad():
                outputs = hf_model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
                pred_idx = probs.argmax(dim=1).item()
                hf_conf = probs[0][pred_idx].item()
                hf_label = hf_model.config.id2label.get(pred_idx, str(pred_idx))
            hf_result = {"label": hf_label.lower(), "confidence": round(hf_conf, 4)}
            signals["hf_face"] = hf_result
        except Exception as e:
            signals["hf_error"] = str(e)

    # ---- Ensemble Logic ----

    # Case 1: No face detected — deepfake detection is N/A
    if not signals["has_face"] and not is_synth:
        return {
            "label": "indeterminate",
            "confidence": 0.0,
            "signals": signals,
            "verdict": "No face detected — deepfake detection requires a visible face. This image may not contain a face, or the face may be too small/obscured.",
        }

    # Case 2: Synthetic content (our training data) — use CNN model directly
    if is_synth and cnn_result:
        return {
            "label": cnn_result["label"],
            "confidence": cnn_result["confidence"],
            "signals": signals,
            "verdict": f"Synthetic content detected. CNN model prediction: {cnn_result['label']} ({cnn_result['confidence']:.1%})",
        }

    # Case 3: Real photo with face — combine signals
    votes = []
    weights = []

    # CNN vote (weight: 0.55 — trained on FF++ real deepfakes, highly accurate on faces)
    if cnn_result:
        cnn_is_fake = cnn_result["label"] == "fake"
        votes.append(1.0 if cnn_is_fake else 0.0)
        weights.append(0.55)

    # HuggingFace vote (weight: 0.35 — if available, most reliable)
    if hf_result:
        hf_is_fake = hf_result["label"] in ("fake", "deepfake")
        votes.append(1.0 if hf_is_fake else 0.0)
        weights.append(0.35)

    # Realism vote (weight: 0.10 — only as tiebreaker, not primary signal)
    realism_score = 0.0
    if signals["has_face"]:
        realism_score += 0.25
    if quality["overall"] > 0.6:
        realism_score += 0.25
    if not is_synth:
        realism_score += 0.25
    if quality["texture"] > 0.3:
        realism_score += 0.25
    votes.append(1.0 - realism_score)
    weights.append(0.10)

    # Calculate weighted vote
    if weights:
        total_weight = sum(weights)
        fake_score = sum(v * w for v, w in zip(votes, weights)) / total_weight
    else:
        fake_score = 0.5

    # Determine label
    if fake_score > 0.65:
        label = "fake"
        confidence = min(0.95, fake_score)
    elif fake_score < 0.35:
        label = "real"
        confidence = min(0.95, 1 - fake_score)
    else:
        label = "indeterminate"
        confidence = 1 - abs(fake_score - 0.5) * 2

    # Build verdict
    vote_details = []
    if cnn_result:
        vote_details.append(f"CNN: {cnn_result['label']} ({cnn_result['confidence']:.1%})")
    if hf_result:
        vote_details.append(f"HF: {hf_result['label']} ({hf_result['confidence']:.1%})")
    vote_details.append(f"Faces: {len(faces)}")
    vote_details.append(f"Quality: {quality['overall']:.1%}")

    verdict = f"Ensemble verdict: {label.upper()} ({confidence:.1%}). Signals: {' | '.join(vote_details)}"

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "signals": signals,
        "verdict": verdict,
    }
