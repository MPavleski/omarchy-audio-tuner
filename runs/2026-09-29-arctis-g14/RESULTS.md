# G14 / Arctis Nova 3 speaker sweep — 2026-09-29

- Laptop: ASUS ROG Zephyrus G14 GA402RK.
- Output: built-in speakers, 100% volume for every measurement.
- Input: SteelSeries Arctis Nova 3 microphone, existing 44% input gain.
- Signal: 12 stepped sine tones, 100–8000 Hz, equal -18 dBFS digital peak; both speaker channels driven.
- Capture: 1.5 seconds per tone, mono PCM, 48 kHz / 16 bit.
- No clipped microphone samples. Audio settings restored and verified after the sweep.

## Interpretation

These are levels recorded by an uncalibrated headset microphone, not calibrated speaker SPL or an isolated speaker response. The microphone, speaker placement, room, and any device processing affect the results. Low-frequency fundamentals are especially weak and their distortion figures should not be used to judge speaker limits or derive bass boosts. High-frequency THD includes fewer harmonics because of the recording bandwidth. No corrective EQ was generated or applied.

## Measurements

| Frequency (Hz) | Fundamental (dBFS) | Capture peak (dBFS) | Reported THD (%) |
|---:|---:|---:|---:|
| 100 | -92.1 | -69.5 | 22.93 |
| 150 | -84.9 | -63.9 | 40.79 |
| 200 | -78.7 | -59.2 | 48.97 |
| 300 | -67.2 | -59.7 | 31.69 |
| 500 | -56.8 | -52.2 | 16.88 |
| 750 | -51.5 | -50.5 | 11.17 |
| 1000 | -46.9 | -45.2 | 7.75 |
| 1500 | -49.0 | -48.2 | 2.44 |
| 2000 | -57.2 | -53.8 | 30.22 |
| 3000 | -44.9 | -44.2 | 0.66 |
| 5000 | -51.6 | -46.5 | 0.80 |
| 8000 | -40.1 | -40.0 | 0.04 |

## Files

- `sweep/`: raw microphone WAV recordings.
- `tones/`: source tone WAV files.
- `sweep-results.json`: measurement results and recording paths.
- `sweep.log`: original toolkit analysis output.
- `sweep-before.json`: saved audio state.
- `sweep-restore.json`: restoration errors (empty).
- `pilot*`: preliminary 1 kHz input-level check.
