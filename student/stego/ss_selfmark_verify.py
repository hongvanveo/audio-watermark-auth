#!/usr/bin/env python3
import argparse
import hashlib
import math
import os
import random
import wave
from array import array
from pathlib import Path


FRAME_LEN = 1024
MAGIC = "SSAUTH"
MAX_SHIFT_FRAMES = 64


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


def write_marker(name):
    Path(name).write_text("done\n", encoding="utf-8")


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
    return rate, [float(value) for value in samples]


def norm(values):
    return math.sqrt(sum(value * value for value in values)) + 1e-12


def evaluate(audio, key, frame_shift):
    bits = payload_bits(key)
    frame_count = len(audio) // FRAME_LEN
    usable = frame_count - frame_shift
    if usable <= len(bits):
        return -1.0, 0.0

    bit_scores = [[] for _ in bits]
    for frame_index in range(usable):
        start = frame_index * FRAME_LEN
        frame = audio[start:start + FRAME_LEN]
        expected_index = (frame_index + frame_shift) % len(bits)
        sign = bits[expected_index]
        pn = pn_sequence(key, expected_index, FRAME_LEN)
        score = sum(frame[i] * pn[i] for i in range(FRAME_LEN)) / (norm(frame) * norm(pn))
        bit_scores[expected_index].append(score * sign)

    collapsed = [sum(scores) / len(scores) for scores in bit_scores if scores]
    if not collapsed:
        return -1.0, 0.0
    average_score = sum(collapsed) / len(collapsed)
    bit_agreement = sum(1 for value in collapsed if value > 0) / len(collapsed)
    return average_score, bit_agreement


def classify(best_score, agreement, shift_frames):
    found = best_score >= 0.12 and agreement >= 0.60
    if not found:
        return "NOT FOUND", "MALICIOUS TAMPERING DETECTED"
    if shift_frames > 0:
        return "FOUND", "MALICIOUS TAMPERING DETECTED"
    if best_score >= 0.16 and agreement >= 0.85:
        return "FOUND", "ACCEPTABLE MODIFICATION"
    if best_score >= 0.10 and agreement >= 0.70:
        return "FOUND", "SUSPICIOUS MODIFICATION"
    return "FOUND", "MALICIOUS TAMPERING DETECTED"


def maybe_mark(path, status):
    name = Path(path).name.lower()
    if name == "volume.wav" and status == "ACCEPTABLE MODIFICATION":
        write_marker(".volume_acceptable_done")
        mark("PASS_VOLUME_ACCEPTABLE")
    if name == "noise.wav" and status == "ACCEPTABLE MODIFICATION":
        write_marker(".noise_acceptable_done")
        mark("PASS_NOISE_ACCEPTABLE")
    if name == "cropped.wav" and status == "MALICIOUS TAMPERING DETECTED":
        write_marker(".crop_malicious_done")
        mark("PASS_CROP_MALICIOUS")


def main():
    parser = argparse.ArgumentParser(description="Verify spread-spectrum self-marking watermark.")
    parser.add_argument("input")
    parser.add_argument("--sign-file")
    parser.add_argument("--key", required=True, type=int)
    args = parser.parse_args()

    if args.sign_file:
        with open(args.sign_file, "rb") as handle:
            message_bytes = handle.read().strip()
    else:
        message_bytes = b"audio watermark auth"
    if not message_bytes:
        raise SystemExit("message rong")
    derived_key = f"{args.key}:{hashlib.sha256(message_bytes).hexdigest()[:16]}"

    _, audio = read_wav(args.input)
    frame_count = len(audio) // FRAME_LEN
    max_shift = min(MAX_SHIFT_FRAMES, max(0, frame_count // 5))

    best_shift = 0
    best_score = -1.0
    best_agreement = 0.0
    for shift in range(max_shift + 1):
        score, agreement = evaluate(audio, derived_key, shift)
        if score > best_score + 0.005 or (
            abs(score - best_score) <= 0.005 and shift < best_shift
        ):
            best_shift = shift
            best_score = score
            best_agreement = agreement

    watermark, status = classify(best_score, best_agreement, best_shift)
    maybe_mark(args.input, status)

    print(f"File: {Path(args.input).name}")
    print(f"Watermark: {watermark}")
    print(f"Status: {status}")
    print(f"Score: {best_score:.3f}")
    print(f"ShiftFrames: {best_shift}")


if __name__ == "__main__":
    main()
