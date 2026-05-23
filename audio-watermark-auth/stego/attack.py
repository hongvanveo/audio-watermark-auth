#!/usr/bin/env python3
import argparse
import math
import random
import wave
from array import array


FRAME_LEN = 1024
LEVELS = {
    "volume": {
        "light": {"factor": 0.9},
        "medium": {"factor": 0.7},
        "heavy": {"factor": 0.5},
    },
    "noise": {
        "light": {"snr": 35.0},
        "medium": {"snr": 25.0},
        "heavy": {"snr": 20.0},
    },
    "crop": {
        "light": {"ratio": 0.02},
        "medium": {"ratio": 0.05},
        "heavy": {"ratio": 0.10},
    },
    "lowpass": {
        "light": {"cutoff": 6000.0},
        "medium": {"cutoff": 4000.0},
        "heavy": {"cutoff": 2500.0},
    },
    "replace": {
        "light": {"ratio": 0.03},
        "medium": {"ratio": 0.08},
        "heavy": {"ratio": 0.15},
    },
    "reorder": {
        "light": {"ratio": 0.04},
        "medium": {"ratio": 0.10},
        "heavy": {"ratio": 0.18},
    },
}


def clamp_pcm16(value):
    return max(-32768, min(32767, int(round(value))))


def read_wav(path):
    with wave.open(path, "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError("chi ho tro WAV mono PCM16")
        rate = wav.getframerate()
        samples = array("h")
        samples.frombytes(wav.readframes(wav.getnframes()))
    return rate, list(samples)


def write_wav(path, rate, samples):
    out = array("h", (clamp_pcm16(value) for value in samples))
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(out.tobytes())


def level_value(kind, level, field):
    return LEVELS[kind][level][field]


def attack_volume(samples, factor):
    return [value * factor for value in samples]


def attack_noise(samples, snr):
    signal_power = sum(value * value for value in samples) / max(1, len(samples))
    noise_power = signal_power / (10 ** (snr / 10.0))
    sigma = math.sqrt(noise_power)
    rng = random.Random(12345)
    return [value + rng.gauss(0.0, sigma) for value in samples]


def attack_crop(samples, ratio):
    frames = len(samples) // FRAME_LEN
    cut_frames = max(1, int(frames * ratio))
    cut = cut_frames * FRAME_LEN
    kept = samples[cut:]
    return kept + [0] * cut


def attack_lowpass(samples, rate, cutoff):
    dt = 1.0 / rate
    rc = 1.0 / (2.0 * math.pi * cutoff)
    alpha = dt / (rc + dt)
    out = []
    prev = samples[0]
    for value in samples:
        prev = prev + alpha * (value - prev)
        out.append(prev)
    return out


def attack_replace(samples, ratio):
    count = max(FRAME_LEN, int(len(samples) * ratio))
    start = max(0, len(samples) // 3)
    end = min(len(samples), start + count)
    out = list(samples)
    for index in range(start, end):
        t = index - start
        out[index] = 14000 * math.sin(2 * math.pi * 880 * t / 44100.0)
    return out


def attack_reorder(samples, ratio):
    frames = len(samples) // FRAME_LEN
    chunk_frames = max(1, int(frames * ratio / 2))
    chunk = chunk_frames * FRAME_LEN
    if chunk <= 0 or len(samples) < chunk * 3:
        return list(samples)
    start_a = FRAME_LEN * 4
    start_b = start_a + chunk
    end_b = start_b + chunk
    out = list(samples)
    a = out[start_a:start_b]
    b = out[start_b:end_b]
    out[start_a:start_b] = b
    out[start_b:end_b] = a
    return out


def main():
    parser = argparse.ArgumentParser(description="Apply audio attacks from one unified script.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--type", required=True, choices=sorted(LEVELS.keys()))
    parser.add_argument("--level", choices=["light", "medium", "heavy"])
    parser.add_argument("--factor", type=float)
    parser.add_argument("--snr", type=float)
    parser.add_argument("--ratio", type=float)
    parser.add_argument("--cutoff", type=float)
    args = parser.parse_args()

    rate, samples = read_wav(args.input)

    if args.type == "volume":
        factor = args.factor if args.factor is not None else level_value("volume", args.level or "light", "factor")
        if not 0.5 <= factor <= 1.5:
            raise SystemExit("factor phai trong khoang 0.5 den 1.5")
        out = attack_volume(samples, factor)
    elif args.type == "noise":
        snr = args.snr if args.snr is not None else level_value("noise", args.level or "light", "snr")
        if not 20.0 <= snr <= 40.0:
            raise SystemExit("snr phai trong khoang 20 den 40 dB")
        out = attack_noise(samples, snr)
    elif args.type == "crop":
        ratio = args.ratio if args.ratio is not None else level_value("crop", args.level or "heavy", "ratio")
        if not 0.02 <= ratio <= 0.20:
            raise SystemExit("ratio phai trong khoang 0.02 den 0.20")
        out = attack_crop(samples, ratio)
    elif args.type == "lowpass":
        cutoff = args.cutoff if args.cutoff is not None else level_value("lowpass", args.level or "light", "cutoff")
        if not 1500.0 <= cutoff <= 8000.0:
            raise SystemExit("cutoff phai trong khoang 1500 den 8000")
        out = attack_lowpass(samples, rate, cutoff)
    elif args.type == "replace":
        ratio = args.ratio if args.ratio is not None else level_value("replace", args.level or "medium", "ratio")
        if not 0.02 <= ratio <= 0.20:
            raise SystemExit("ratio phai trong khoang 0.02 den 0.20")
        out = attack_replace(samples, ratio)
    else:
        ratio = args.ratio if args.ratio is not None else level_value("reorder", args.level or "medium", "ratio")
        if not 0.02 <= ratio <= 0.20:
            raise SystemExit("ratio phai trong khoang 0.02 den 0.20")
        out = attack_reorder(samples, ratio)

    write_wav(args.output, rate, out)
    print(f"created={args.output}")


if __name__ == "__main__":
    main()
