#!/usr/bin/env python3
import subprocess
import sys


COMMANDS = [
    ["ss_selfmark_embed.py", "cover.wav", "marked_ss.wav", "--key", "12345"],
    ["attack.py", "marked_ss.wav", "volume.wav", "--type", "volume", "--factor", "0.8"],
    ["attack.py", "marked_ss.wav", "noise.wav", "--type", "noise", "--snr", "30"],
    ["attack.py", "marked_ss.wav", "cropped.wav", "--type", "crop", "--ratio", "0.1"],
    ["ss_selfmark_verify.py", "volume.wav", "--key", "12345"],
    ["ss_selfmark_verify.py", "noise.wav", "--key", "12345"],
    ["ss_selfmark_verify.py", "cropped.wav", "--key", "12345"],
]


def main():
    for command in COMMANDS:
        full = [sys.executable, *command]
        print("$", " ".join(["python3", *command]))
        subprocess.run(full, check=True)


if __name__ == "__main__":
    main()
