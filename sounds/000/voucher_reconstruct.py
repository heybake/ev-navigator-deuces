
"""Auto-generated module to reproduce audio.

- Sample rate: 44100 Hz
- Channels: 1
- This module provides get_samples() and play().
"""

import numpy as np
def get_samples():
    """Return float32 samples in [-1,1]."""
    return np.load(r"G:\My Drive\Temp\EV Navigator Deuces Wild\ev-navigator-deuces\sounds\voucher_samples.npy")


def play(samples=None, sr=44100):
    """Play samples (float32) using sounddevice. If samples is None, uses get_samples()."""
    try:
        import sounddevice as sd
    except Exception as e:
        raise RuntimeError("sounddevice is required to play audio: " + str(e))
    if samples is None:
        samples = get_samples()
    samples = np.asarray(samples, dtype=np.float32)
    # simple normalization guard
    peak = max(1e-9, float(np.max(np.abs(samples))))
    if peak > 1.0:
        samples = samples / peak * 0.95
    sd.play(samples, sr)
    sd.wait()
