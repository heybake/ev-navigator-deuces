import wave
import math
import struct
import os
import random

# CONFIG
SAMPLE_RATE = 44100
VOLUME = 0.5

def write_wav(filename, samples):
    """Writes raw audio samples to a .wav file."""
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
        
    path = os.path.join("sounds", filename)
    with wave.open(path, "w") as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes (16-bit)
        wav_file.setframerate(SAMPLE_RATE)
        
        # Pack data
        data = b""
        for s in samples:
            # Clip to 16-bit range
            s = max(-32767, min(32767, int(s * 32767 * VOLUME)))
            data += struct.pack("<h", s)
            
        wav_file.writeframes(data)
    print(f"🔊 Generated: {path}")

def generate_tone(freq, duration, decay=True):
    """Generates a sine wave."""
    samples = []
    num_samples = int(duration * SAMPLE_RATE)
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        val = math.sin(2.0 * math.pi * freq * t)
        if decay:
            val *= (1.0 - (i / num_samples)) # Linear decay
        samples.append(val)
    return samples

def generate_noise(duration):
    """Generates white noise (for card thwip)."""
    samples = []
    num_samples = int(duration * SAMPLE_RATE)
    for i in range(num_samples):
        val = random.uniform(-1, 1) * (1.0 - (i / num_samples))
        samples.append(val)
    return samples

# --- SOUND RECIPES ---

def make_bet_sound():
    # A high "Ding" (Coin insert)
    return generate_tone(1200, 0.1)

def make_deal_sound():
    # A fast "Thwip" (Card snap)
    # Mix of noise and a snap tone
    noise = generate_noise(0.08)
    tone = generate_tone(300, 0.08)
    return [n*0.7 + t*0.3 for n, t in zip(noise, tone)]

def make_win_sound():
    # A Major Triad (C-E-G) "Ta-Da!"
    c = generate_tone(523.25, 0.1)
    e = generate_tone(659.25, 0.1)
    g = generate_tone(783.99, 0.4)
    return c + e + g

def make_rollup_sound():
    # A continuous fast "ding-ding" for the meter count
    tone = generate_tone(880, 0.08) # A5
    silence = [0] * int(0.05 * SAMPLE_RATE)
    return tone + silence

if __name__ == "__main__":
    print("🎹 Synthesizing Casino Audio...")
    write_wav("bet.wav", make_bet_sound())
    write_wav("deal.wav", make_deal_sound())
    write_wav("win.wav", make_win_sound())
    write_wav("rollup.wav", make_rollup_sound())
    print("✅ Done! Sounds are ready in 'sounds/' folder.")