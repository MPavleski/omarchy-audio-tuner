# ASUS G14 speaker EQ

Installed for the internal ALSA device
`alsa_output.pci-0000_77_00.6.analog-stereo` only. USB headsets, HDMI, and
Bluetooth outputs are not processed. Per user preference there is no
headphone-jack monitoring: the analog jack shares this internal device.

The selectable virtual output is **Laptop Speakers (G14 EQ)**.

## Profile

- Low shelf: +3 dB, 150 Hz, Q 0.707 (user requested).
- Peak cut: -3 dB, 3 kHz, Q 1.2 (conservative trial based on the repeated peak).
- Overall headroom: -3 dB. Bass is boosted relative to midrange; with this
  headroom, deep-bass absolute gain is approximately 0 dB versus the raw path.
- Stereo LSP lookahead limiter: -1 dBFS threshold, automatic gain and makeup off.

The Arctis headset microphone is uncalibrated. This is a provisional listening
profile, not a validated correction of the laptop speaker response.

## Controls

```bash
g14-speaker-eq status
g14-speaker-eq off
g14-speaker-eq on
```

The user service starts with the graphical session. Its filter output is pinned
to the named internal device with `node.dont-move`, `node.dont-fallback`, and
`node.linger`. Startup selects EQ only if the internal device was selected,
and moves only streams on that device. Selecting USB/HDMI uses those outputs
directly. Selecting the raw internal output manually bypasses EQ.

## Installed files

- `~/.config/pipewire/g14-speaker-eq.conf`
- `~/.config/systemd/user/g14-speaker-eq.service`
- `~/.local/lib/g14-speaker-eq/route.py`
- `~/.local/bin/g14-speaker-eq`

After editing the installed EQ config:

```bash
systemctl --user restart g14-speaker-eq.service
```

## Verification

The live filter was measured by comparing the physical output monitor with and
without EQ using a 104-tone probe, with the physical speakers muted. Maximum
response deviation from the configured biquads and headroom was 0.009 dB.
See `verification/response.json` and the original captures in that directory.
This validates filter operation, not acoustic correction. The physical speaker
volume and all temporarily changed mute states were restored after testing.

Original routing state is saved in `before-install.json`.
