#!/usr/bin/env python3
import argparse
import hashlib
import math
import os
import random
import struct
import wave
from array import array


FRAME_LEN = 1024
STRENGTH = 0.18
MAGIC = "SSAUTH"


def mark(token):
    result = os.path.expanduser("~/.local/result/watermark_auth_check.txt")
    os.makedirs(os.path.dirname(result), exist_ok=True)
    existing = ""
    if os.path.exists(result):
        with open(result, "r", encoding="utf-8") as handle:
            existing = handle.read()
    if token not in existing:
        with open(result, "a", encoding="utf-8") as handle:
            handle.write(token + "\n")


def clamp_pcm16(value):
    return max(-32768, min(32767, int(round(value))))


def payload_bits(key):
    digest = hashlib.sha256(f"{MAGIC}:{key}".encode("utf-8")).digest()
    raw = MAGIC.encode("ascii")[:2] + digest[:4]
    bits = []
    for byte in raw:
        for shift in range(7, -1, -1):
            bits.append(1 if (byte >> shift) & 1 else -1)
    return bits


def pn_sequence(key, bit_index, length):
    seed = int(hashlib.sha256(f"{key}:{bit_index}".encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    return [1.0 if rng.random() >= 0.5 else -1.0 for _ in range(length)]


def read_wav(path):
    with wave.open(path, "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError("chi ho tro WAV mono PCM16")
        rate = wav.getframerate()
        samples = array("h")
        samples.frombytes(wav.readframes(wav.getnframes()))
    return rate, samples


def write_wav(path, rate, samples):
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())


def main():
    parser = argparse.ArgumentParser(description="Embed spread-spectrum self-marking watermark.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--key", required=True, type=int)
    args = parser.parse_args()

    rate, samples = read_wav(args.input)
    frame_count = len(samples) // FRAME_LEN
    if frame_count < 24:
        raise SystemExit("audio qua ngan cho watermark")

    bits = payload_bits(args.key)
    audio = [float(value) for value in samples]
    rms = math.sqrt(sum(value * value for value in audio) / max(1, len(audio)))
    alpha = rms * STRENGTH

    for frame_index in range(frame_count):
        start = frame_index * FRAME_LEN
        bit_index = frame_index % len(bits)
        sign = bits[bit_index]
        pn = pn_sequence(args.key, bit_index, FRAME_LEN)
        for offset in range(FRAME_LEN):
            audio[start + offset] += sign * alpha * pn[offset]

    out = array("h", (clamp_pcm16(value) for value in audio))
    write_wav(args.output, rate, out)
    mark("PASS_MARKED_CREATED")
    print(f"marked={args.output}")


if __name__ == "__main__":
    main()
