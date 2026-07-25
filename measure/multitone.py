#!/usr/bin/env python3
"""Generate the multitone probe used to measure a speaker path.

  ./multitone.py gen dense.wav

Every tone is an integer number of Hz, so with a one-second analysis window at
48 kHz each lands exactly on a DFT bin. That makes the measurement leakage-free
and avoids the skirt bias a third-octave bandpass has wherever the response has a
steep gradient -- an error that read +1.5 dB at 100 Hz on hardware where a sine
said -3.1 dB.

The tones are dense (one per twelfth-octave) and pink-weighted, so the composite
resembles music closely enough that a compressor in the path under test behaves
as it does on programme material.

Writes the tone list next to the wav as dense-freqs.txt, which analyse-dense.py
reads back.
"""

import math
import os
import random
import struct
import sys
import wave

FS = 48000

# Generated files go to a writable cache dir, because once this is installed as a
# package the script's own directory is read-only.
CACHE = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "omarchy-audio-tuner")
FREQ_LIST = os.path.join(CACHE, "dense-freqs.txt")


def frequencies():
    out, f = [], 40.0
    while f <= 16000:
        i = int(round(f))
        if i not in out:
            out.append(i)
        f *= 2 ** (1 / 12)
    return out


def gen(path, seconds=6, target_lufs=-14.0):
    freqs = frequencies()
    rng = random.Random(7)
    phases = [rng.uniform(0, 2 * math.pi) for _ in freqs]
    # Pink weighting: amplitude proportional to 1/sqrt(f) gives equal energy per
    # octave, which is roughly how music distributes its energy.
    amps = [1 / math.sqrt(f) for f in freqs]

    one = []
    for n in range(FS):
        one.append(sum(a * math.sin(2 * math.pi * f * n / FS + p)
                       for f, a, p in zip(freqs, amps, phases)))

    peak = max(abs(v) for v in one)
    # Leave headroom so the probe itself never clips a path under test.
    scale = (10 ** (-6 / 20)) / peak

    frames = bytearray()
    for _ in range(seconds):
        for v in one:
            s = int(max(-1.0, min(1.0, v * scale)) * 32767)
            frames += struct.pack("<hh", s, s)

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(bytes(frames))

    os.makedirs(CACHE, exist_ok=True)
    with open(FREQ_LIST, "w") as fh:
        fh.write("\n".join(str(f) for f in freqs) + "\n")

    print(f"wrote {path}: {len(freqs)} pink-weighted tones, "
          f"{freqs[0]}-{freqs[-1]} Hz, composite peak -6 dBFS")
    print(f"wrote {FREQ_LIST}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "gen":
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    gen(sys.argv[2])
