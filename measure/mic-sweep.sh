#!/usr/bin/env bash
set -euo pipefail

# Sweep speaker level and measure acoustic distortion at a fixed tone.
#
#   mic-sweep.sh <sink> <tone.wav> <freq-hz> <label>
#
# Routing is done by switching the default sink, because mpv's --audio-device
# silently falls back to the default when the device string does not resolve,
# which would measure the wrong signal path.

sink="$1"
tone="$2"
freq="$3"
label="$4"
here="$(cd -- "$(dirname -- "$0")" && pwd)"

# Default to the system's chosen input and the internal speaker sink, so this
# runs on any laptop rather than only the machine it was written on. Override the
# microphone with MIC=<source-name> when the default input is not the measurement
# mic.
mic="${MIC:-$(pactl get-default-source)}"
hw="${SPEAKER_SINK:-$(pactl list sinks short |
  awk '$2 ~ /^alsa_output.*(sof_sdw|HiFi).*Speaker.*sink$/ {print $2; exit}')}"
[[ -n $hw ]] || {
  echo "No internal speaker sink found." >&2
  exit 1
}

previous_default="$(pactl get-default-sink)"
previous_volume="$(pactl get-sink-volume "$hw" | awk 'NR==1 {print $3}')"
previous_mute="$(pactl get-sink-mute "$hw" | awk '{print $2}')"
previous_mic_volume="$(pactl get-source-volume "$mic" | awk 'NR==1 {print $3}')"
previous_mic_mute="$(pactl get-source-mute "$mic" | awk '{print $2}')"
out_dir="${OUT_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-audio-tuner/spectral}"
mkdir -p "$out_dir"
read -ra levels <<< "${LEVELS:-40 55 70 85 100}"
for pct in "${levels[@]}"; do
  [[ $pct =~ ^[0-9]+$ ]] && ((pct >= 1 && pct <= 100)) || {
    echo "Invalid volume percentage: $pct" >&2
    exit 2
  }
done
restore() {
  [[ -n ${player:-} ]] && kill "$player" 2>/dev/null || true
  pactl set-default-sink "$previous_default" 2>/dev/null || true
  pactl set-sink-volume "$hw" "$previous_volume" 2>/dev/null || true
  pactl set-sink-mute "$hw" "$previous_mute" 2>/dev/null || true
  pactl set-source-volume "$mic" "$previous_mic_volume" 2>/dev/null || true
  pactl set-source-mute "$mic" "$previous_mic_mute" 2>/dev/null || true
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

pactl set-default-sink "$sink"
pactl set-sink-volume "$hw" "${levels[0]}%"
pactl set-sink-mute "$hw" 0
pactl set-source-mute "$mic" 0
# Keep the selected input gain unless explicitly overridden; 100% can clip.
[[ -z ${MIC_VOLUME:-} ]] || pactl set-source-volume "$mic" "$MIC_VOLUME"

mpv --no-config --volume=100 --no-video --no-terminal --really-quiet --loop-file=inf --ao=pulse --audio-device="pulse/$sink" "$tone" &
player=$!
sleep 2

want="$(pactl list sinks short | awk -v n="$sink" '$2 == n {print $1; exit}')"
landed="$(pactl -f json list sink-inputs | python3 -c '
import json, sys
for stream in json.load(sys.stdin):
    if str(stream.get("properties", {}).get("application.process.id")) == sys.argv[1]:
        print(stream["sink"])
        break
' "$player")"
[[ -n $want && $landed == "$want" ]] || {
  printf 'Tone landed on sink %s, expected %s (%s).\n' "$landed" "$want" "$sink" >&2
  exit 1
}

printf '\n%s @ %s Hz\n' "$label" "$freq"
printf '%5s  %s\n' "vol" "microphone"
for pct in "${levels[@]}"; do
  pactl set-sink-volume "$hw" "$((65536 * pct / 100))"
  sleep 1.2
  cap="$out_dir/mic-$label-$freq-$pct.wav"
  ffmpeg -hide_banner -loglevel error -y -f pulse -i "$mic" \
    -t 1.5 -ac 1 -ar 48000 -acodec pcm_s16le "$cap"
  printf '%4s%%  %s\n' "$pct" "$(python3 "$here/analyze-tone.py" "$cap" "$freq")"
done
