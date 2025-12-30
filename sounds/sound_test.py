import wave
import math
import struct
import random
import os

# Parameters
filename = "wild_deuce.wav"
duration = 1.5  # seconds
sample_rate = 44100  # Hz
frequency = 440  # Base frequency (A4)
volume = 0.5  # Range: 0.0 to 1.0

# Create wave file
with wave.open(filename, 'w') as wav_file:
    wav_file.setnchannels(1)  # mono
    wav_file.setsampwidth(2)  # 2 bytes per sample
    wav_file.setframerate(sample_rate)

    for i in range(int(duration * sample_rate)):
        # Add chaotic modulation
        mod = math.sin(2 * math.pi * i / sample_rate * random.uniform(2, 6))
        freq = frequency + mod * 50

        # Generate sample
        sample = volume * math.sin(2 * math.pi * freq * i / sample_rate)

        # Convert to 16-bit PCM
        packed_sample = struct.pack('<h', int(sample * 32767))
        wav_file.writeframes(packed_sample)

print(f"Generated {filename}")