#!/usr/bin/env python3
"""Measure a tone's fundamental and harmonics in a mono 16-bit wav.

Capture length is chosen so the fundamental and every harmonic fall exactly on
a DFT bin, which makes the Goertzel evaluation leakage-free without windowing.
Harmonic ratios are valid through a non-flat microphone as long as comparisons
are made at the same frequencies, which is why this can characterise distortion
versus level with a mic that has no calibration file.
"""

import math
import struct
import sys
import wave


def read_mono(path):
    with wave.open(path, "rb") as w:
        assert w.getsampwidth() == 2, "expected 16-bit"
        n = w.getnframes()
        raw = w.readframes(n)
        ch = w.getnchannels()
        data = struct.unpack("<%dh" % (len(raw) // 2), raw)
        if ch > 1:
            data = [sum(data[i:i + ch]) / ch for i in range(0, len(data), ch)]
        return list(data), w.getframerate()


def goertzel(samples, fs, freq):
    n = len(samples)
    k = freq * n / fs
    if abs(k - round(k)) > 1e-6:
        # Not bin-aligned; fall back to a direct DFT term.
        w = 2 * math.pi * freq / fs
        re = sum(s * math.cos(w * i) for i, s in enumerate(samples))
        im = -sum(s * math.sin(w * i) for i, s in enumerate(samples))
        return 2 * math.hypot(re, im) / n
    w = 2 * math.pi * round(k) / n
    coeff = 2 * math.cos(w)
    s1 = s2 = 0.0
    for s in samples:
        s0 = s + coeff * s1 - s2
        s2, s1 = s1, s0
    re = s1 - s2 * math.cos(w)
    im = s2 * math.sin(w)
    return 2 * math.hypot(re, im) / n


def main():
    path, f0 = sys.argv[1], float(sys.argv[2])
    samples, fs = read_mono(path)
    full = 32768.0

    amps = []
    for h in range(1, 7):
        f = f0 * h
        if f > fs / 2 * 0.95:
            amps.append(0.0)
            continue
        amps.append(goertzel(samples, fs, f))

    fund = amps[0]
    harm = math.sqrt(sum(a * a for a in amps[1:]))
    thd = (harm / fund * 100) if fund > 0 else float("nan")

    def db(a):
        return 20 * math.log10(a / full) if a > 0 else -999

    parts = " ".join(f"h{h}={db(a):7.1f}" for h, a in enumerate(amps[1:], 2))
    print(f"fund={db(fund):7.1f} dBFS  {parts}  THD={thd:6.2f}%")


if __name__ == "__main__":
    main()
