# slow_receipt_printer.py
# Requires: numpy, sounddevice
# Run: python slow_receipt_printer.py

import time
import numpy as np
import sounddevice as sd
import random
import sys

# ----------------- User tweakable parameters -----------------
SAMPLE_RATE = 44100
DURATION = 6.0                # total audio duration in seconds (approx)
TICK_VOLUME = 0.18            # loudness of each dot tick
TICK_FREQ_MIN = 3800         # tick frequency range (Hz)
TICK_FREQ_MAX = 6200
TICK_COUNT = 120             # number of ticks across the print duration
TICK_LENGTH_MIN = 18         # tick length in samples
TICK_LENGTH_MAX = 36
NOISE_LEVEL = 0.0008         # paper feed hiss level (very low)
SWEEP_DEPTH = 180            # small pitch sweep for head motion
CHUNK_VOLUME = 0.45          # cutter/clamp volume
CHUNK_FREQ = 120             # cutter pitch (low mechanical)
LINE_DELAY = 0.12            # seconds between printed lines (slower = more dot-matrix feel)
TICK_PER_LINE = 6            # approximate number of ticks to play per printed line
TICK_CHAR = '.'              # character to show as each tick in console (visual flourish)
# --------------------------------------------------------------

# Example receipt content
RECEIPT_LINES = [
    "THE CRAWL CASINO",
    "EV NAVIGATOR - DEUCES WILD",
    "TABLE 7 - SESSION 42",
    "--------------------------------",
    "1x ROYAL FLUSH BONUS     $500.00",
    "3x DEUCE WILD JACKPOT     $75.00",
    "CASH OUT                 $575.00",
    "--------------------------------",
    "THANK YOU FOR PLAYING",
    "VISIT AGAIN",
]

def make_square_wave(freq, length, sample_rate):
    t = np.arange(length)
    return np.sign(np.sin(2 * np.pi * freq * t / sample_rate))

def synth_printer_audio(duration=DURATION, sample_rate=SAMPLE_RATE):
    samples = int(duration * sample_rate)
    audio = np.zeros(samples)

    # semi-regular tick positions with slight jitter
    base_positions = np.linspace(0, samples * 0.88, TICK_COUNT).astype(int)
    jitter = (np.random.randn(len(base_positions)) * (sample_rate * 0.002)).astype(int)
    tick_positions = np.clip(base_positions + jitter, 0, samples - 1)

    for i, t in enumerate(tick_positions):
        freq = random.randint(TICK_FREQ_MIN, TICK_FREQ_MAX)
        sweep_dir = 1 if (i % 2 == 0) else -1
        length = random.randint(TICK_LENGTH_MIN, TICK_LENGTH_MAX)
        freqs = freq + sweep_dir * np.linspace(0, SWEEP_DEPTH, length)
        tick = np.zeros(length)
        for j, f in enumerate(freqs):
            tick[j] = np.sign(np.sin(2 * np.pi * f * j / sample_rate))
        # quick decay for each tick
        tick *= TICK_VOLUME * np.exp(-np.linspace(0, 3.5, length))
        end = min(t + length, samples)
        audio[t:end] += tick[:end - t]

    # very light paper feed hiss
    noise = np.random.randn(samples) * NOISE_LEVEL
    kernel = np.ones(64) / 64.0
    low = np.convolve(noise, kernel, mode='same')
    audio += (noise - low)

    # final cutter chunk near the end
    chunk_start = int(samples * 0.92)
    chunk_len = samples - chunk_start
    if chunk_len > 0:
        chunk = CHUNK_VOLUME * np.sign(np.sin(2 * np.pi * CHUNK_FREQ * np.arange(chunk_len) / sample_rate))
        env = np.concatenate([np.linspace(0, 1, min(40, chunk_len)), np.exp(-np.linspace(0, 3, max(0, chunk_len - 40)))])
        chunk *= env[:chunk_len]
        audio[chunk_start:] += chunk

    # normalize
    max_val = np.max(np.abs(audio)) + 1e-9
    audio = audio / max_val * 0.95
    return audio

def play_and_print_receipt(lines=RECEIPT_LINES,
                           line_delay=LINE_DELAY,
                           ticks_per_line=TICK_PER_LINE,
                           tick_char=TICK_CHAR):
    # synth audio buffer
    audio = synth_printer_audio()
    # start playback asynchronously
    sd.play(audio, SAMPLE_RATE)

    # compute tick schedule to roughly align with audio
    total_ticks = TICK_COUNT
    ticks_assigned = 0
    ticks_for_lines = []
    for i in range(len(lines)):
        # allocate ticks proportionally, ensure at least 1 tick per line
        remaining_lines = len(lines) - i
        remaining_ticks = total_ticks - ticks_assigned
        allocate = max(1, int(remaining_ticks / remaining_lines))
        ticks_for_lines.append(allocate)
        ticks_assigned += allocate

    # print lines slowly, showing small tick characters as visual feedback
    for idx, line in enumerate(lines):
        # print the line
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

        # show small tick animation for the allocated ticks
        for _ in range(ticks_for_lines[idx]):
            sys.stdout.write(tick_char)
            sys.stdout.flush()
            time.sleep(line_delay / max(1, ticks_for_lines[idx]))
        # newline after ticks for readability
        sys.stdout.write("\n")
        sys.stdout.flush()

    # wait for audio to finish
    sd.wait()

if __name__ == "__main__":
    print("\n--- Printing receipt (dot-matrix slow) ---\n")
    play_and_print_receipt()
    print("\n--- Receipt complete ---\n")