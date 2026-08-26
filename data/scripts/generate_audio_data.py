"""Generate synthetic real vs cloned audio dataset for Phase 4."""

import numpy as np
import soundfile as sf
from pathlib import Path

OUT = Path("data/audio")
REAL = OUT / "real"
FAKE = OUT / "fake"
REAL.mkdir(parents=True, exist_ok=True)
FAKE.mkdir(parents=True, exist_ok=True)

SR = 16000
DURATION = 2.0  # seconds
N_SAMPLES = 300  # 150 real + 150 fake

rng = np.random.default_rng(42)


def _make_real(idx: int) -> np.ndarray:
    """Natural speech-like signal: harmonics + formants + noise."""
    t = np.linspace(0, DURATION, int(SR * DURATION), dtype=np.float32)
    # Fundamental + harmonics (formants)
    f0 = rng.uniform(80, 300)
    sig = np.zeros_like(t)
    for h in range(1, 8):
        amp = rng.uniform(0.1, 0.5) / h
        sig += amp * np.sin(2 * np.pi * f0 * h * t + rng.uniform(0, 2 * np.pi))
    # Amplitude modulation (prosody)
    mod_freq = rng.uniform(2, 6)
    sig *= 0.5 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
    # Add natural noise
    sig += rng.normal(0, 0.02, len(t)).astype(np.float32)
    return (sig / np.abs(sig).max() * 0.8).astype(np.float32)


def _make_fake(idx: int) -> np.ndarray:
    """Synthetic/clone artifacts: phase discontinuities, metallic buzz, periodic glitches."""
    t = np.linspace(0, DURATION, int(SR * DURATION), dtype=np.float32)
    f0 = rng.uniform(80, 300)
    sig = np.zeros_like(t)
    for h in range(1, 8):
        # Fake: inconsistent phase per harmonic
        phase = rng.uniform(0, 2 * np.pi)
        sig += (rng.uniform(0.1, 0.5) / h) * np.sin(2 * np.pi * f0 * h * t + phase)
    # Metallic buzz (high-freq artifact)
    sig += 0.3 * np.sin(2 * np.pi * rng.uniform(6000, 8000) * t).astype(np.float32)
    # Periodic glitches (clicking artifacts common in voice clones)
    n_glitches = rng.integers(5, 15)
    for _ in range(n_glitches):
        pos = rng.integers(0, len(sig))
        sig[max(0, pos - 5):min(len(sig), pos + 5)] += rng.uniform(-0.5, 0.5)
    return (sig / max(np.abs(sig).max(), 1e-8) * 0.8).astype(np.float32)


print(f"Generating {N_SAMPLES} audio samples...")
for i in range(N_SAMPLES):
    sf.write(REAL / f"real_{i:04d}.wav", _make_real(i), SR)
    sf.write(FAKE / f"fake_{i:04d}.wav", _make_fake(i), SR)

print(f"Done: {N_SAMPLES} real + {N_SAMPLES} fake at {OUT}")
