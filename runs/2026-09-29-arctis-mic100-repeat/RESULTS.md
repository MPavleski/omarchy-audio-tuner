# Arctis 100% input — repeated short sweep

Both speaker volume and microphone input were 100%. Test tones were -18 dBFS peak. This repeat followed the user’s request after identifying the previous run’s incorrect microphone placement.

## Quiet baseline

| Recording | RMS (dBFS) | Peak (dBFS) |
|---|---:|---:|
| quiet-original-gain.wav | -75.8 | -58.3 |
| quiet-test-gain-after.wav | -62.4 | -48.4 |
| quiet-test-gain.wav | -56.7 | -38.4 |

## Test tones

| Frequency (Hz) | Fundamental (dBFS) | Capture peak (dBFS) |
|---:|---:|---:|
| 100 | -74.4 | -49.9 |
| 200 | -59.5 | -44.4 |
| 1000 | -25.8 | -24.9 |

## Interpretation

No clipped samples were found. More input gain raises background noise along with the tones; it does not establish improved acoustic signal-to-noise ratio. The recorded 100 Hz fundamental remains about 49 dB below 1 kHz, and 200 Hz about 34 dB below it. This is the combined speaker, microphone, placement, and room response—not proof of a headset EQ or a calibrated speaker measurement. Background recordings include ambient sound, not only microphone self-noise. Low-frequency THD estimates are not dependable for tuning from this test.

Original speaker and microphone channel volumes, mute states, default devices, and pre-existing stream mute states were verified restored.

Raw WAV files are in `sweep/`; quiet recordings are alongside this report. Detailed measurements are in `sweep-results.json` and `noise-results.json`.
