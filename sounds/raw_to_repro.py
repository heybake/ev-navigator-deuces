#!/usr/bin/env python3
"""
raw_to_repro.py

Reads a signed 16-bit little-endian RAW PCM file and produces:
  - a normalized NumPy .npy file of float32 samples in [-1,1]
  - an optional WAV export
  - an auto-generated Python module that loads/returns/plays the samples

Usage examples:
  python raw_to_repro.py --input input.raw --sr 44100 --channels 1 --outprefix voucher
  python raw_to_repro.py --input input.raw --sr 48000 --channels 2 --outprefix voucher --embed-threshold 50000

Options:
  --input         Path to RAW file (s16le)
  --sr            Sample rate to assume (default 44100)
  --channels      1 or 2 (default 1)
  --outprefix     Prefix for outputs (default 'reconstructed')
  --save-wav      If set, also write a 16-bit WAV file
  --embed-threshold  If sample count <= threshold, embed samples as Python literal in generated module (default 0 = do not embed)
"""

import argparse
import numpy as np
import wave
import os
import textwrap

def load_raw_s16le(path, channels=1):
    data = np.fromfile(path, dtype=np.int16)
    if channels == 2:
        if data.size % 2 != 0:
            raise ValueError("Stereo RAW length is not even; check file or channels parameter.")
        data = data.reshape(-1, 2)
    return data

def normalize_to_float32(int16_arr):
    # int16 -> float32 in [-1,1)
    return (int16_arr.astype(np.float32) / 32768.0)

def save_npy(path, arr):
    np.save(path, arr.astype(np.float32))
    print(f"Saved .npy: {path}")

def save_wav(path, arr, sr=44100):
    # arr expected float32 in [-1,1], mono or stereo
    arr = np.asarray(arr)
    if arr.ndim == 1:
        channels = 1
        frames = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
    else:
        channels = arr.shape[1]
        interleaved = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        frames = interleaved.tobytes()
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)
    print(f"Saved WAV: {path}")

def generate_module(out_module_path, npy_path, sr, channels, embed_samples=None):
    """
    Create a Python module that exposes:
      - get_samples() -> numpy array float32
      - play() -> plays via sounddevice (if available)
    If embed_samples is provided (1D or 2D float array), embed as literal.
    """
    module_name = os.path.basename(out_module_path)
    embed_code = ""
    load_code = textwrap.dedent(f"""
        import numpy as np
        def get_samples():
            \"\"\"Return float32 samples in [-1,1].\"\"\"
            return np.load(r\"{npy_path}\")
    """)
    if embed_samples is not None:
        # embed as Python literal (careful with large arrays)
        arr = np.asarray(embed_samples, dtype=np.float32)
        if arr.ndim == 1:
            literal = np.array2string(arr, separator=', ', max_line_width=120)
            embed_code = textwrap.dedent(f"""
                import numpy as np
                def get_samples():
                    # Embedded {arr.size} samples (float32)
                    return np.array({literal}, dtype=np.float32)
            """)
        else:
            # 2D stereo
            literal = np.array2string(arr, separator=', ', max_line_width=120)
            embed_code = textwrap.dedent(f"""
                import numpy as np
                def get_samples():
                    # Embedded stereo array shape {arr.shape}
                    return np.array({literal}, dtype=np.float32)
            """)
        load_code = embed_code

    play_code = textwrap.dedent("""
        def play(samples=None, sr=%d):
            \"\"\"Play samples (float32) using sounddevice. If samples is None, uses get_samples().\"\"\"
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
    """ % (sr))

    header = textwrap.dedent(f"""
    \"\"\"Auto-generated module to reproduce audio.

    - Sample rate: {sr} Hz
    - Channels: {channels}
    - This module provides get_samples() and play().
    \"\"\"
    """)
    with open(out_module_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(load_code)
        f.write("\n")
        f.write(play_code)
    print(f"Generated module: {out_module_path}")

def main():
    p = argparse.ArgumentParser(description="Convert RAW s16le -> .npy + reconstruct module")
    p.add_argument('--input', '-i', required=True, help="Input RAW file (s16le)")
    p.add_argument('--sr', type=int, default=44100, help="Sample rate to assume (Hz)")
    p.add_argument('--channels', type=int, default=1, choices=[1,2], help="1=mono, 2=stereo")
    p.add_argument('--outprefix', '-o', default='reconstructed', help="Output prefix")
    p.add_argument('--save-wav', action='store_true', help="Also write a WAV file")
    p.add_argument('--embed-threshold', type=int, default=0,
                   help="If sample count <= threshold, embed samples as Python literal in generated module (default 0 = no embed)")
    args = p.parse_args()

    raw_path = args.input
    sr = args.sr
    channels = args.channels
    outprefix = args.outprefix
    save_wav_flag = args.save_wav
    embed_threshold = args.embed_threshold

    if not os.path.exists(raw_path):
        raise SystemExit(f"Input RAW not found: {raw_path}")

    print("Loading RAW...")
    raw = load_raw_s16le(raw_path, channels=channels)
    print("Raw shape:", raw.shape)

    print("Converting to float32 [-1,1]...")
    float_samples = normalize_to_float32(raw)

    # If stereo interleaved int16 was loaded as shape (N,2), float_samples will be same shape
    npy_out = f"{outprefix}_samples.npy"
    save_npy(npy_out, float_samples)

    if save_wav_flag:
        wav_out = f"{outprefix}.wav"
        save_wav(wav_out, float_samples, sr=sr)

    # Decide whether to embed samples in module
    embed = None
    total_samples = float_samples.shape[0] if float_samples.ndim == 1 else float_samples.shape[0] * float_samples.shape[1]
    if embed_threshold > 0 and total_samples <= embed_threshold:
        embed = float_samples
        print(f"Embedding {total_samples} samples into generated module (threshold {embed_threshold}).")
    else:
        print(f"Not embedding samples (total_samples={total_samples}, threshold={embed_threshold}).")

    module_path = f"{outprefix}_reconstruct.py"
    # Use absolute path for npy load inside module to avoid relative path issues
    npy_abs = os.path.abspath(npy_out)
    generate_module(module_path, npy_abs, sr, channels, embed_samples=embed)

    print("\nDone. Outputs:")
    print(f" - NumPy samples: {os.path.abspath(npy_out)}")
    if save_wav_flag:
        print(f" - WAV file: {os.path.abspath(wav_out)}")
    print(f" - Reconstruct module: {os.path.abspath(module_path)}")
    print("\nHow to use the generated module in your game:")
    print(textwrap.dedent(f"""
      from {os.path.splitext(os.path.basename(module_path))[0]} import get_samples, play
      samples = get_samples()   # numpy float32 array in [-1,1]
      # play(samples)           # plays via sounddevice
      # or mix/process samples as you like in your game audio engine
    """))

if __name__ == "__main__":
    main()