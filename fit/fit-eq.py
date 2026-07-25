#!/usr/bin/env python3
"""Fit a biquad chain to a measured target curve read from <freq> <delta-dB>.

Cascaded biquads multiply in magnitude, so their dB contributions add. Each
section's dB curve is cached and only the changed section is recomputed, which
makes coordinate descent over a 14-section chain tractable in pure Python.
"""

import cmath
import math
import random
import sys

FS = 48000.0


def biquad(kind, f0, q, gain_db):
    w0 = 2 * math.pi * f0 / FS
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2 * q)
    if kind == "peaking":
        a = 10 ** (gain_db / 40)
        return ([1 + alpha * a, -2 * cw, 1 - alpha * a],
                [1 + alpha / a, -2 * cw, 1 - alpha / a])
    if kind == "highpass":
        return ([(1 + cw) / 2, -(1 + cw), (1 + cw) / 2],
                [1 + alpha, -2 * cw, 1 - alpha])
    a = 10 ** (gain_db / 40)
    beta = 2 * math.sqrt(a) * alpha
    if kind == "lowshelf":
        return ([a * ((a + 1) - (a - 1) * cw + beta),
                 2 * a * ((a - 1) - (a + 1) * cw),
                 a * ((a + 1) - (a - 1) * cw - beta)],
                [(a + 1) + (a - 1) * cw + beta,
                 -2 * ((a - 1) + (a + 1) * cw),
                 (a + 1) + (a - 1) * cw - beta])
    return ([a * ((a + 1) + (a - 1) * cw + beta),
             -2 * a * ((a - 1) + (a + 1) * cw),
             a * ((a + 1) + (a - 1) * cw - beta)],
            [(a + 1) - (a - 1) * cw + beta,
             2 * ((a - 1) - (a + 1) * cw),
             (a + 1) - (a - 1) * cw - beta])


def section_db(kind, f0, q, g, zs):
    b, a = biquad(kind, f0, q, g)
    out = []
    for z in zs:
        h = (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)
        out.append(20 * math.log10(abs(h)))
    return out


LAYOUT = [
    ("highpass", (40, 110), (0.4, 1.6), (0, 0)),
    ("highpass", (28, 80), (0.4, 1.6), (0, 0)),
    ("peaking", (60, 105), (0.8, 5.0), (-10, 4)),
    ("peaking", (100, 150), (0.8, 5.0), (-4, 8)),
    ("peaking", (170, 300), (0.5, 3.0), (-10, 4)),
    ("peaking", (300, 470), (0.5, 3.0), (-10, 4)),
    ("peaking", (480, 780), (0.5, 4.0), (-16, 2)),
    ("peaking", (800, 1120), (0.6, 4.0), (-8, 6)),
    ("peaking", (1150, 1500), (0.8, 5.0), (-4, 8)),
    ("peaking", (1550, 2250), (0.5, 4.0), (-14, 2)),
    ("peaking", (2300, 3100), (0.5, 4.0), (-12, 4)),
    ("peaking", (3200, 5000), (0.5, 3.0), (-8, 6)),
    ("highshelf", (4000, 10000), (0.4, 1.5), (-8, 10)),
]


def weight(f):
    if f < 55:
        return 0.5
    if f > 12000:
        return 0.6
    return 1.0


def fit(freqs, target, zs, ws, seed):
    rng = random.Random(seed)
    secs, cache = [], []
    for kind, fr, qr, gr in LAYOUT:
        s = [kind,
             math.exp(rng.uniform(math.log(fr[0]), math.log(fr[1]))),
             rng.uniform(*qr),
             0.0 if kind == "highpass" else rng.uniform(*gr)]
        secs.append(s)
        cache.append(section_db(s[0], s[1], s[2], s[3], zs))
    gain = rng.uniform(-8, 8)

    def total_err():
        num = den = 0.0
        for i, f in enumerate(freqs):
            got = gain + sum(c[i] for c in cache)
            num += ws[i] * (got - target[i]) ** 2
            den += ws[i]
        return num / den

    best = total_err()
    step = {"f": 0.3, "q": 0.5, "g": 3.0, "gain": 3.0}
    for _ in range(300):
        improved = False
        for i, (kind, fr, qr, gr) in enumerate(LAYOUT):
            for key, lo, hi in (("f", fr[0], fr[1]), ("q", qr[0], qr[1]),
                                ("g", gr[0], gr[1])):
                if key == "g" and kind == "highpass":
                    continue
                idx = {"f": 1, "q": 2, "g": 3}[key]
                for d in (1, -1):
                    old = secs[i][idx]
                    new = old * math.exp(d * step["f"]) if key == "f" \
                        else old + d * step[key]
                    new = min(max(new, lo), hi)
                    if new == old:
                        continue
                    oldc = cache[i]
                    secs[i][idx] = new
                    cache[i] = section_db(secs[i][0], secs[i][1], secs[i][2],
                                          secs[i][3], zs)
                    e = total_err()
                    if e < best - 1e-9:
                        best, improved = e, True
                        break
                    secs[i][idx] = old
                    cache[i] = oldc
        for d in (1, -1):
            old = gain
            gain = old + d * step["gain"]
            e = total_err()
            if e < best - 1e-9:
                best, improved = e, True
                break
            gain = old
        if not improved:
            for k in step:
                step[k] *= 0.62
            if step["f"] < 5e-5:
                break
    return best, secs, gain


def main():
    target_path = sys.argv[1]
    rows = [l.split() for l in open(target_path)]
    freqs = [float(r[0]) for r in rows]
    target = [float(r[1]) for r in rows]
    zs = [cmath.exp(-2j * math.pi * f / FS) for f in freqs]
    ws = [weight(f) for f in freqs]

    best = None
    for seed in range(int(sys.argv[2]) if len(sys.argv) > 2 else 12):
        r = fit(freqs, target, zs, ws, seed)
        if best is None or r[0] < best[0]:
            best = r
    err, secs, gain = best
    print(f"# weighted RMS error: {math.sqrt(err):.2f} dB")
    print(f"# global gain: {gain:+.3f} dB  (linear {10 ** (gain / 20):.4f})")
    for kind, f0, q, g in secs:
        if kind == "highpass":
            print(f'{kind:10s} Freq={f0:8.1f} Q={q:.3f}')
        else:
            print(f'{kind:10s} Freq={f0:8.1f} Q={q:.3f} Gain={g:+.2f}')
    cache = [section_db(s[0], s[1], s[2], s[3], zs) for s in secs]
    print("\n# freq  target    fit    err")
    for i, f in enumerate(freqs):
        if i % 6:
            continue
        got = gain + sum(c[i] for c in cache)
        print(f"{f:7.0f} {target[i]:+7.1f} {got:+7.1f} {got - target[i]:+6.1f}")


if __name__ == "__main__":
    main()
