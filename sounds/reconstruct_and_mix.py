"""
reconstruct_and_mix.py

Usage examples:
  python reconstruct_and_mix.py --input samples.txt --format auto --sr 44100 --out reconstructed.wav
  python reconstruct_and_mix.py --input samples.csv --format int16 --sr 22050 --play
  # Or import functions from this file in your game and call load_samples(...) directly.
"""

import argparse
import numpy as np
import sounddevice as sd
import wave
import os

# -------------------------
# Utilities
# -------------------------
def detect_dtype_and_normalize(arr):
    """Detect if arr is int16-like or float-like and return float32 in [-1,1] and dtype string."""
    arr = np.asarray(arr)
    if np.issubdtype(arr.dtype, np.integer):
        # assume int16 range
        return arr.astype(np.float32) / 32768.0, 'int16'
    # floats: check range
    maxabs = np.max(np.abs(arr)) if arr.size else 0.0
    if maxabs > 1.5:
        # values look like int16 but stored as floats
        return (arr.astype(np.float32) / 32768.0), 'int16-like-float'
    return arr.astype(np.float32), 'float32'

def load_samples_from_text(path, delimiter=None):
    """Load samples from a text file. Handles one-per-line or comma-separated."""
    # Use numpy loadtxt which handles whitespace or comma if delimiter provided
    try:
        if delimiter is None:
            # try to auto-detect comma vs newline
            with open(path, 'rb') as f:
                head = f.read(4096)
            if b',' in head:
                delimiter = ','
        data = np.loadtxt(path, delimiter=delimiter, dtype=np.float64)
    except Exception as e:
        # fallback: read as single-line CSV
        txt = open(path, 'r', encoding='utf-8', errors='ignore').read().strip()
        if ',' in txt:
            parts = txt.split(',')
        else:
            parts = txt.split()
        data = np.array([float(p) for p in parts], dtype=np.float64)
    return data

def load_samples_from_npy(path):
    return np.load(path)

def save_wav(path, audio, sr=44100):
    """Save float32 mono audio in [-1,1] to 16-bit PCM WAV."""
    audio = np.asarray(audio)
    if audio.ndim == 2 and audio.shape[1] == 2:
        channels = 2
    else:
        channels = 1
        audio = audio.flatten()
    # clip and convert
    audio_i16 = np.clip(audio, -1.0, 1.0)
    audio_i16 = (audio_i16 * 32767.0).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_i16.tobytes())
    print(f"Saved WAV: {path}")

def play_audio(audio, sr=44100):
    """Play float32 audio with sounddevice. Accepts mono or stereo."""
    audio = np.asarray(audio, dtype=np.float32)
    peak = np.max(np.abs(audio)) + 1e-9
    if peak > 1.0:
        audio = audio / peak * 0.95
    sd.play(audio, sr)
    sd.wait()

# -------------------------
# Procedural printer + coin generator
# -------------------------
def generate_printer_and_coins(duration, sr=44100,
                               tick_base_freq=4800, tick_jitter=600,
                               tick_density=0.0025, tick_vol=0.18,
                               coin_count=30, coin_vol=0.16):
    """Generate a procedural slow dot-matrix printer sound with a coin cascade."""
    samples = int(duration * sr)
    proc = np.zeros(samples, dtype=np.float32)
    rng = np.random.default_rng()

    # continuous dot-matrix texture
    tick_len = max(6, int(0.018 * sr))  # ~18 ms default tick length
    for i in range(0, samples):
        if rng.random() < tick_density:
            freq = int(tick_base_freq + rng.integers(-tick_jitter, tick_jitter))
            length = rng.integers(int(0.012*sr), int(0.035*sr))  # 12-35 ms
            t = np.arange(length)
            # sharp square-like tick using sign of sine
            tick = np.sign(np.sin(2 * np.pi * freq * t / sr)).astype(np.float32)
            env = np.exp(-np.linspace(0, 4.0, length))
            tick = tick * env * tick_vol
            end = min(i + length, samples)
            proc[i:end] += tick[:end - i]

    # coin cascade placed in the latter half
    coin_start = int(samples * 0.45)
    for _ in range(coin_count):
        start = coin_start + rng.integers(0, max(1, samples - coin_start - 200))
        freq = rng.integers(2500, 4000)
        length = rng.integers(int(0.02*sr), int(0.08*sr))
        t = np.arange(length)
        ping = np.sin(2 * np.pi * freq * t / sr).astype(np.float32)
        decay = np.exp(-np.linspace(0, 5.0, length))
        ping = ping * decay * coin_vol * rng.random()
        end = min(start + length, samples)
        proc[start:end] += ping[:end - start]

    # light paper hiss
    proc += (rng.standard_normal(samples) * 0.0009).astype(np.float32)

    # normalize conservatively
    maxv = np.max(np.abs(proc)) + 1e-9
    proc = proc / maxv * 0.95
    return proc

# -------------------------
# Main high-level functions
# -------------------------
def reconstruct_from_numbers(numbers,
                             sample_rate=44100,
                             input_dtype_hint=None,
                             out_wav=None,
                             play=False,
                             mix_with_proc=False,
                             proc_level=0.9,
                             real_level=0.7):
    """
    numbers: numpy array of ints or floats
    sample_rate: sample rate in Hz
    input_dtype_hint: 'int16' or 'float' or None
    out_wav: path to save reconstructed WAV
    play: whether to play immediately
    mix_with_proc: whether to mix with procedural printer+coins
    """
    arr = np.asarray(numbers)
    # detect and normalize
    if input_dtype_hint == 'int16' or np.issubdtype(arr.dtype, np.integer):
        audio, dtype = detect_dtype_and_normalize(arr)
    else:
        # floats or unknown
        audio, dtype = detect_dtype_and_normalize(arr)

    print(f"Detected input type: {dtype}; samples: {audio.shape[0]}; sr: {sample_rate}")

    final = audio.copy()

    if mix_with_proc:
        proc = generate_printer_and_coins(duration=audio.shape[0] / sample_rate, sr=sample_rate)
        # trim/pad
        min_len = min(len(proc), len(final))
        proc = proc[:min_len]
        final = final[:min_len]
        mixed = final * real_level + proc * proc_level
        # normalize
        mixed = mixed / (np.max(np.abs(mixed)) + 1e-9) * 0.95
        final = mixed

    if out_wav:
        save_wav(out_wav, final, sr=sample_rate)

    if play:
        play_audio(final, sr=sample_rate)

    return final

# -------------------------
# Command line interface
# -------------------------
def main():
    p = argparse.ArgumentParser(description="Reconstruct audio from numeric samples and optionally mix/play/save.")
    p.add_argument('--input', '-i', required=True, help="Path to input numeric file (.txt, .csv, .npy) or raw .raw (s16le).")
    p.add_argument('--format', choices=['auto','int16','float','raw_s16le','npy'], default='auto',
                   help="Input format. 'raw_s16le' treats file as raw int16 PCM.")
    p.add_argument('--sr', type=int, default=44100, help="Sample rate to assume or use for playback.")
    p.add_argument('--channels', type=int, default=1, help="Channels for raw_s16le input (1 or 2).")
    p.add_argument('--out', '-o', help="Optional output WAV path to save reconstructed audio.")
    p.add_argument('--play', action='store_true', help="Play the reconstructed audio.")
    p.add_argument('--mix', action='store_true', help="Mix with procedural printer+coins layer.")
    args = p.parse_args()

    path = args.input
    fmt = args.format
    sr = args.sr

    if fmt == 'npy' or path.lower().endswith('.npy'):
        samples = load_samples_from_npy(path)
    elif fmt == 'raw_s16le' or path.lower().endswith('.raw'):
        # load raw int16
        data = np.fromfile(path, dtype=np.int16)
        if args.channels == 2:
            data = data.reshape(-1, 2)
        samples = data
    else:
        # text or csv
        samples = load_samples_from_text(path)

    reconstruct_from_numbers(samples,
                             sample_rate=sr,
                             input_dtype_hint=None,
                             out_wav=args.out,
                             play=args.play,
                             mix_with_proc=args.mix)

if __name__ == "__main__":
    main()