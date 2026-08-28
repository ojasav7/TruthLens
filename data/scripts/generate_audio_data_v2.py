"""
V2 Audio data generator — realistic speech-like signals + voice clone artifacts.

Improvements:
- More realistic harmonic structure with formant frequencies
- Natural prosody and breathing patterns
- Realistic clone artifacts: phase discontinuities, spectral envelope mismatch
- Varied durations and speaking rates

Usage:
    python data/scripts/generate_audio_data_v2.py --n_per_class 500
"""

import argparse
import numpy as np
import soundfile as sf
from pathlib import Path

SR = 16000
RNG = np.random.default_rng(42)

# Formant frequencies (Hz) for realistic vowel-like sounds
FORMANTS = [
    (300, 850, 2400),    # /a/
    (400, 1000, 2550),   # /e/
    (350, 1200, 2700),   # /i/
    (300, 870, 2250),    # /o/
    (350, 700, 2300),    # /u/
]


def _make_real(duration=2.0):
    """Realistic speech-like signal with formants, prosody, and breathing."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    # Fundamental frequency (varies over time — prosody)
    f0_base = RNG.uniform(100, 250)
    # Add natural pitch variation (intonation contour)
    prosody = 1 + 0.05 * np.sin(2 * np.pi * RNG.uniform(1, 4) * t)
    f0 = f0_base * prosody

    sig = np.zeros(n, dtype=np.float32)

    # Harmonics with formant shaping
    formant = FORMANTS[RNG.integers(0, len(FORMANTS))]
    for h in range(1, 20):
        # Amplitude shaped by formant resonance
        formant_amp = sum(1.0 / (1.0 + ((h * f0_base - f) / 100) ** 2) for f in formant)
        amp = (RNG.uniform(0.3, 0.7) / h) * formant_amp / 3
        phase = RNG.uniform(0, 2 * np.pi)
        sig += amp * np.sin(2 * np.pi * f0 * h * t + phase)

    # Amplitude envelope (speech-like bursts)
    envelope = np.ones(n, dtype=np.float32)
    n_bursts = RNG.integers(3, 8)
    for _ in range(n_bursts):
        start = RNG.integers(0, n - SR // 4)
        length = RNG.integers(SR // 8, SR // 2)
        end = min(start + length, n)
        attack = min(RNG.integers(50, 200), end - start)
        # Fade in
        envelope[start:start + attack] *= np.linspace(0, 1, attack)
        # Fade out
        fade_len = min(RNG.integers(50, 200), end - start - attack)
        if fade_len > 0:
            envelope[end - fade_len:end] *= np.linspace(1, 0, fade_len)

    sig *= envelope

    # Breathing noise (very quiet, adds realism)
    breath_mask = np.zeros(n, dtype=np.float32)
    n_breaths = RNG.integers(0, 3)
    for _ in range(n_breaths):
        pos = RNG.integers(0, n - SR // 4)
        length = RNG.integers(SR // 8, SR // 4)
        breath_mask[pos:pos + length] = 1.0
    breath_mask = np.convolve(breath_mask, np.hanning(SR // 32), mode="same")
    sig += breath_mask * RNG.normal(0, 0.03, n).astype(np.float32)

    # Natural background noise
    sig += RNG.normal(0, 0.01, n).astype(np.float32)

    return (sig / max(np.abs(sig).max(), 1e-8) * 0.8).astype(np.float32)


def _make_fake(duration=2.0):
    """Voice clone artifacts: spectral envelope mismatch, phase discontinuities, metallic tone."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    f0_base = RNG.uniform(100, 250)

    sig = np.zeros(n, dtype=np.float32)

    # Harmonics with inconsistent phase (clone artifact)
    for h in range(1, 15):
        amp = RNG.uniform(0.2, 0.6) / h
        # Key artifact: phase discontinuities at random points
        phase = RNG.uniform(0, 2 * np.pi)
        sig += amp * np.sin(2 * np.pi * f0_base * h * t + phase)

    # Metallic resonance (high-frequency artifact from vocoder)
    metal_freq = RNG.uniform(4000, 7000)
    sig += 0.15 * np.sin(2 * np.pi * metal_freq * t + RNG.uniform(0, 2 * np.pi))

    # Spectral envelope mismatch: energy concentrated in wrong frequency bands
    # Real speech has energy below 4kHz; clones often have energy spread higher
    hf_noise = RNG.normal(0, 0.08, n).astype(np.float32)
    # Bandpass 3-7 kHz (unnatural for speech)
    from scipy.signal import butter, sosfilt
    sos = butter(4, [3000, 7000], btype="band", fs=SR, output="sos")
    hf_filtered = sosfilt(sos, hf_noise)
    sig += hf_filtered

    # Periodic glitches (clicking from concatenation artifacts)
    n_glitches = RNG.integers(8, 25)
    for _ in range(n_glitches):
        pos = RNG.integers(0, n)
        width = RNG.integers(3, 15)
        sig[max(0, pos - width):min(n, pos + width)] += RNG.uniform(-0.4, 0.4)

    # Inconsistent amplitude (clones often have flat or jumpy dynamics)
    if RNG.random() < 0.5:
        # Unnatural flatness
        sig = sig / max(np.abs(sig).max(), 1e-8) * 0.7
    else:
        # Sudden amplitude jumps
        jump_pos = RNG.integers(n // 4, 3 * n // 4)
        sig[jump_pos:] *= RNG.uniform(0.3, 2.0)

    return (sig / max(np.abs(sig).max(), 1e-8) * 0.8).astype(np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_per_class", type=int, default=500)
    parser.add_argument("--output", type=str, default="data/audio_v2")
    args = parser.parse_args()

    output = Path(args.output)
    real_dir = output / "real"
    fake_dir = output / "fake"
    real_dir.mkdir(parents=True, exist_ok=True)
    fake_dir.mkdir(parents=True, exist_ok=True)

    n = args.n_per_class
    print(f"Generating {n} real + {n} fake audio samples...")

    for i in range(n):
        # Varied durations
        dur = RNG.uniform(1.5, 3.0)
        sf.write(str(real_dir / f"real_{i:04d}.wav"), _make_real(dur), SR)
        sf.write(str(fake_dir / f"fake_{i:04d}.wav"), _make_fake(dur), SR)

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{n}")

    print(f"Done: {len(list(real_dir.glob('*.wav')))} real, {len(list(fake_dir.glob('*.wav')))} fake")


if __name__ == "__main__":
    main()
