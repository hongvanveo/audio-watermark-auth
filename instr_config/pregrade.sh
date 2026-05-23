#!/bin/bash
homedir=$1
destdir=$2

workdir="$homedir/$destdir/stego"
resultdir="$homedir/$destdir/.local/result"
result="$resultdir/watermark_auth_check.txt"

mkdir -p "$resultdir"
: > "$result"

pass() { echo "PASS_$1" >> "$result"; }
fail() { echo "FAIL_$1: $2" >> "$result"; }

if [ -s "$workdir/cover.wav" ]; then
    pass "COVER_AVAILABLE"
else
    fail "COVER_AVAILABLE" "cover.wav missing"
fi

if [ -s "$workdir/marked_ss.wav" ]; then
    pass "MARKED_CREATED"
else
    fail "MARKED_CREATED" "marked_ss.wav missing"
fi

if [ -s "$workdir/.volume_acceptable_done" ]; then
    pass "VOLUME_ACCEPTABLE"
else
    fail "VOLUME_ACCEPTABLE" "volume verification not completed"
fi

if [ -s "$workdir/.noise_acceptable_done" ]; then
    pass "NOISE_ACCEPTABLE"
else
    fail "NOISE_ACCEPTABLE" "noise verification not completed"
fi

if [ -s "$workdir/.crop_malicious_done" ]; then
    pass "CROP_MALICIOUS"
else
    fail "CROP_MALICIOUS" "crop verification not completed"
fi
