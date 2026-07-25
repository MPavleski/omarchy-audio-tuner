#!/usr/bin/env bash
set -euo pipefail

# Play the multitone probe into a sink and record the result.
#
#   ./capture.sh [--from monitor|<source>] [--seconds N] <sink> <out.wav>
#
# Recording from the sink monitor (the default) measures the DSP electrically and
# is independent of the room, the speakers and listening level, because a sink's
# monitor sits upstream of its volume control. Recording from a microphone source
# instead measures what the speakers actually produce, which is what you need
# when there is no reference chain to copy -- but see the calibration warning in
# docs/AUDIO-TUNING.md before deriving an EQ target that way.

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# The probe is generated, so it lives in a writable cache dir rather than beside
# the script, which is read-only once this is installed as a package.
cache="${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-audio-tuner"
probe="$cache/dense.wav"
source_name=""
seconds=2

while (($#)); do
  case "$1" in
    --from)
      source_name="$2"
      shift
      ;;
    --seconds)
      seconds="$2"
      shift
      ;;
    -h | --help)
      sed -n '5,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      if [[ -z ${sink:-} ]]; then sink="$1"; else out="$1"; fi
      ;;
  esac
  shift
done

[[ -n ${sink:-} && -n ${out:-} ]] || {
  echo "Usage: ./capture.sh [--from monitor|<source>] [--seconds N] <sink> <out.wav>" >&2
  exit 2
}

[[ -r $probe ]] || {
  echo "Generating the probe signal first..." >&2
  mkdir -p "$cache"
  "$here/multitone.py" gen "$probe" >&2
}

# Capture from the *physical* speaker sink, not from the sink being played into.
# A sink's monitor carries what it receives, so recording a DSP sink's own monitor
# measures the signal before its processing and every measurement comes back
# identical. The physical sink is where both the raw and the processed signal end
# up, so its monitor is the right tap in both cases -- and it sits upstream of the
# volume control, so the result is independent of listening level.
if [[ -z $source_name || $source_name == monitor ]]; then
  speakers="$(pactl list sinks short |
    awk '$2 ~ /^alsa_output.*(sof_sdw|HiFi).*Speaker.*sink$/ {print $2; exit}')"
  [[ -n $speakers ]] || {
    echo "No internal speaker sink found; pass --from <source> explicitly." >&2
    exit 1
  }
  source_name="$speakers.monitor"
fi

mpv --no-video --no-terminal --really-quiet --volume=100 --loop-file=inf \
  --ao=pulse --audio-device="pulse/$sink" "$probe" &
player=$!
trap 'kill $player 2>/dev/null || true' EXIT
sleep 3

# mpv falls back to the default sink when an --audio-device string does not
# resolve, and EasyEffects moves streams aimed at a speaker sink to itself. Both
# would measure the wrong path silently, so confirm where the probe landed.
want="$(pactl list sinks short | awk -v n="$sink" '$2 == n {print $1; exit}')"
landed="$(pactl list sink-inputs | awk '
  /^Sink Input #/ {s = ""}
  /^[[:space:]]*Sink:/ {s = $2}
  /application\.name = "mpv"/ {print s; exit}')"
[[ -n $want ]] || {
  echo "No such sink: $sink" >&2
  exit 1
}
[[ $landed == "$want" ]] || {
  echo "Probe landed on sink ${landed:-none}, expected $want ($sink)." >&2
  exit 1
}

ffmpeg -hide_banner -loglevel error -y -f pulse -i "$source_name" \
  -t "$seconds" -ac 2 -ar 48000 -acodec pcm_s16le "$out"

kill $player 2>/dev/null || true
trap - EXIT
printf 'wrote %s (from %s)\n' "$out" "$source_name"
