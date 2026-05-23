#!/usr/bin/env python3
import argparse
import math
import os
import wave
from array import array


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="cover.wav")
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--rate", type=int, default=44100)
    args = parser.parse_args()

    samples = array("h")
    total = int(args.seconds * args.rate)
    for index in range(total):
        t = index / args.rate
        value = 0.38 * math.sin(2 * math.pi * 440 * t)
        value += 0.21 * math.sin(2 * math.pi * 660 * t)
        value += 0.15 * math.sin(2 * math.pi * 880 * t)
        value += 0.08 * math.sin(2 * math.pi * 1760 * t)
        samples.append(int(value * 25000))

    with wave.open(args.out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(args.rate)
        wav.writeframes(samples.tobytes())

    mark("PASS_COVER_AVAILABLE")
    print(f"created={args.out}")


if __name__ == "__main__":
    main()
