# Final G14 / Arctis sweep — 100% microphone input

Completed 12 stepped sine measurements from 100 Hz to 8 kHz.

- Output: ASUS G14 built-in speakers, 100% volume.
- Input: Arctis Nova 3 USB boom microphone, 100% input (0 dB software attenuation).
- Test signal: -18 dBFS digital peak, identical on left/right speakers.
- Each tone capture: 1.5 seconds, mono PCM, 48 kHz / 16 bit.
- Quiet captures: three seconds each, before and after input adjustment and after the sweep.
- Original speaker and microphone channel volumes, mute states, default devices, and existing stream mutes were verified restored.

## Captured tone levels

| Frequency (Hz) | Fundamental (dBFS) | Peak (dBFS) | Reported THD (%) |
|---:|---:|---:|---:|
| 100 | -74.9 | -47.4 | 39.66 |
| 150 | -63.9 | -45.9 | 28.77 |
| 200 | -58.9 | -41.8 | 27.42 |
| 300 | -47.0 | -39.0 | 29.05 |
| 500 | -36.7 | -33.5 | 13.48 |
| 750 | -30.8 | -27.1 | 6.96 |
| 1000 | -26.3 | -24.8 | 4.23 |
| 1500 | -32.8 | -31.2 | 5.45 |
| 2000 | -29.2 | -27.6 | 9.97 |
| 3000 | -20.5 | -19.2 | 0.30 |
| 5000 | -27.8 | -25.8 | 0.81 |
| 8000 | -31.9 | -30.5 | 0.14 |

## Quiet baseline

| Recording | RMS (dBFS) | Peak (dBFS) |
|---|---:|---:|
| quiet-original-gain.wav | -82.2 | -68.7 |
| quiet-test-gain-after.wav | -61.7 | -48.7 |
| quiet-test-gain.wav | -60.4 | -44.5 |

## Interpretation

Clipped samples: 0. Highest tone-recording peak: -19.2 dBFS.

These measurements include the speaker, uncalibrated microphone, placement, room, and any device processing. They are not calibrated SPL measurements. The 100 Hz fundamental is about 49 dB below the 1 kHz fundamental despite equal source levels. Increased microphone gain has not resolved that relative bass deficit. Its cause cannot be assigned to the microphone or speakers from this test alone.

The quiet recordings include ambient sound as well as microphone/electronics noise. Very weak bass fundamentals make low-frequency THD estimates unreliable. High-frequency THD covers fewer harmonics due to the recording bandwidth. No corrective EQ or bass boost was applied.

## Raw data

- `sweep/`: twelve captured tone WAVs.
- `tones/`: generated source WAVs.
- `quiet-*.wav`: background recordings.
- `sweep-results.json`, `noise-results.json`: numerical results.
- `sweep.log`: toolkit output.
- `sweep-before.json`, `sweep-restore.json`: saved audio state and restoration status.
