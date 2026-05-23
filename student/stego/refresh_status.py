#!/usr/bin/env python3
from pathlib import Path


WORKDIR = Path.home() / "stego"
RESULT = Path.home() / ".local" / "result" / "watermark_auth_check.txt"


def main():
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    tokens = []
    if (WORKDIR / "cover.wav").is_file() and (WORKDIR / "cover.wav").stat().st_size > 0:
        tokens.append("PASS_COVER_AVAILABLE")
    if (WORKDIR / "marked_ss.wav").is_file() and (WORKDIR / "marked_ss.wav").stat().st_size > 0:
        tokens.append("PASS_MARKED_CREATED")
    if (WORKDIR / ".volume_acceptable_done").is_file():
        tokens.append("PASS_VOLUME_ACCEPTABLE")
    if (WORKDIR / ".noise_acceptable_done").is_file():
        tokens.append("PASS_NOISE_ACCEPTABLE")
    if (WORKDIR / ".crop_malicious_done").is_file():
        tokens.append("PASS_CROP_MALICIOUS")
    RESULT.write_text("\n".join(tokens) + ("\n" if tokens else ""), encoding="utf-8")


if __name__ == "__main__":
    main()
