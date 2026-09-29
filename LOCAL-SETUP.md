# G14 and Arctis Nova 3 setup

Checkout: upstream commit `d202897da8e730690d8d3a78f95d7d339393c458`.
The packaged toolkit and `lsp-plugins-lv2` are installed separately.

Local changes in `measure/mic-sweep.sh` add `SPEAKER_SINK`, `LEVELS`,
`OUT_DIR`, and optional `MIC_VOLUME` overrides, check routing by player PID,
disable mpv user configuration, and restore microphone and speaker settings.
The local runner additionally saves exact channel volumes and mutes existing
streams on the speaker sink during the test, restoring them afterward.

## Repeat the frequency sweep

Position the unmuted Arctis boom microphone a few centimetres from one laptop
speaker and keep it fixed. The following command plays audible tones at 100%
speaker volume. Each source tone has a digital peak of -18 dBFS; this is not a
full-scale stress test. The microphone uses its current input gain.

```bash
cd /playground/omarchy-audio-tuner
python3 measure/g14-arctis-sweep.py --run \
  --directory "runs/$(date +%Y%m%d-%H%M%S)-arctis-g14"
```

Add `--pilot` for only a 1 kHz microphone-level check. Use a new output
directory for each repeat. Ctrl+C stops the run and restores settings.

The runner requires the G14's built-in speaker port and the Arctis Nova 3
USB microphone. It generates tones and records 12 frequencies from 100 Hz
through 8 kHz, checks routing, and stops if recordings clip or are effectively
silent. It writes raw WAV recordings, logs, JSON results, and the saved state.

The first completed sweep is documented in
`runs/2026-09-29-arctis-g14/RESULTS.md`. A headset microphone is uncalibrated;
these results do not establish a corrective EQ or safe bass-boost limits.
