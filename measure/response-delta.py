#!/usr/bin/env python3
"""Subtract two measured responses to get a target curve.

  ./response-delta.py raw.txt reference.txt > target.txt

Prints `reference - raw` per frequency, which is the curve a tuning has to
produce to turn the first path into the second. Both inputs are the output of
analyse-dense.py.

When both were captured through the same microphone in the same position, the
microphone's own response cancels in the subtraction, so an uncalibrated mic is
fine here. It is *not* fine for deriving a target from a single absolute
measurement -- see docs/AUDIO-TUNING.md.
"""

import sys


def read(path):
    out = {}
    for line in open(path):
        parts = line.split()
        if len(parts) == 2:
            out[int(parts[0])] = float(parts[1])
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)

    a, b = read(sys.argv[1]), read(sys.argv[2])
    shared = sorted(set(a) & set(b))
    if not shared:
        print("No frequencies in common.", file=sys.stderr)
        sys.exit(1)

    for f in shared:
        print(f"{f} {b[f] - a[f]:.2f}")


if __name__ == "__main__":
    main()
