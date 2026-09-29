#!/usr/bin/env python3
"""Run the local G14/Arctis measurement at 100% speaker volume.

Requires the microphone to be positioned and the listener ready. Test files
are -18 dBFS peak sine waves; speaker volume is 100%, microphone gain unchanged.
All changed audio settings are saved and restored, including on interruption.
"""
import argparse
import array
import json
import math
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
SINK = 'alsa_output.pci-0000_77_00.6.analog-stereo'
MIC = 'alsa_input.usb-SteelSeries_Arctis_Nova_3-00.analog-stereo'
FREQUENCIES = [100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 5000, 8000]


def pactl(*args):
    return subprocess.check_output(['pactl', *args], text=True).strip()


def devices(kind):
    return json.loads(pactl('-f', 'json', 'list', kind))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', required=True)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--frequencies', type=int, nargs='+')
    parser.add_argument('--mic-volume', type=int, choices=range(1, 101), metavar='1-100')
    parser.add_argument('--noise-baseline', action='store_true',
                        help='Record 3 seconds of room noise before and after changing input gain')
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    out = args.directory.resolve()
    out.mkdir(parents=True, exist_ok=True)
    frequencies = args.frequencies or ([1000] if args.pilot else FREQUENCIES)
    if any(f < 40 or f > 16000 for f in frequencies):
        parser.error('Test frequencies must be between 40 and 16000 Hz')
    (out / 'tones').mkdir(exist_ok=True)
    for freq in frequencies:
        tone = out / 'tones' / f'{freq}.wav'
        if not tone.is_file():
            frames = bytearray()
            for n in range(48000):
                sample = round(32767 * 10**(-18/20) * math.sin(2*math.pi*freq*n/48000))
                frames.extend(struct.pack('<hh', sample, sample))
            with wave.open(str(tone), 'wb') as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(48000)
                w.writeframes(frames)
    sink = next(d for d in devices('sinks') if d['name'] == SINK)
    mic = next(d for d in devices('sources') if d['name'] == MIC)
    if sink.get('active_port') != 'analog-output-speaker':
        raise SystemExit('Built-in speaker port is not selected.')
    streams = [s for s in devices('sink-inputs') if s['sink'] == sink['index']]
    state = {'sink': sink, 'microphone': mic, 'streams': streams,
             'default_sink': pactl('get-default-sink'),
             'default_source': pactl('get-default-source'),
             'speaker_percent': 100, 'tone_peak_dbfs': -18,
             'test_mic_percent': args.mic_volume,
             'frequencies_hz': frequencies}
    stem = 'pilot' if args.pilot else 'sweep'
    statefile = out / f'{stem}-before.json'
    if statefile.exists():
        raise SystemExit(f'Refusing to overwrite an existing run: {statefile}')
    statefile.write_text(json.dumps(state, indent=2) + '\n')
    child = None
    results = []

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for stream in streams:
            pactl('set-sink-input-mute', str(stream['index']), '1')
        pactl('set-source-mute', MIC, '0')

        def baseline(name):
            nonlocal child
            print(f'Recording quiet baseline: {name} (3 seconds)...', flush=True)
            child = subprocess.Popen(
                ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin',
                 '-f', 'pulse', '-i', MIC, '-t', '3', '-ac', '1', '-ar', '48000',
                 '-acodec', 'pcm_s16le', str(out / f'{name}.wav')],
                start_new_session=True)
            code = child.wait(timeout=15)
            child = None
            if code:
                raise RuntimeError(f'Baseline capture failed: {name}')

        if args.noise_baseline:
            baseline('quiet-original-gain')
        if args.mic_volume is not None:
            pactl('set-source-volume', MIC, f'{args.mic_volume}%')
        if args.noise_baseline:
            baseline('quiet-test-gain')
        env = dict(os.environ, SPEAKER_SINK=SINK, MIC=MIC, LEVELS='100',
                   OUT_DIR=str(out / stem))
        env.pop('MIC_VOLUME', None)
        with (out / f'{stem}.log').open('w') as log:
            for freq in frequencies:
                print(f'Measuring {freq} Hz at 100% speaker volume...', flush=True)
                child = subprocess.Popen(
                    ['bash', str(ROOT / 'measure/mic-sweep.sh'), SINK,
                     str(out / 'tones' / f'{freq}.wav'), str(freq), 'g14-arctis'],
                    env=env, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True)
                code = child.wait(timeout=25)
                child = None
                if code:
                    raise RuntimeError(f'Measurement failed: see {log.name}')
                recording = out / stem / f'mic-g14-arctis-{freq}-100.wav'
                with wave.open(str(recording)) as w:
                    samples = array.array('h', w.readframes(w.getnframes()))
                    if sys.byteorder != 'little':
                        samples.byteswap()
                peak = max(abs(v) for v in samples)
                rms = math.sqrt(sum(v*v for v in samples) / len(samples))
                analysis = subprocess.check_output(
                    [sys.executable, str(ROOT / 'measure/analyze-tone.py'),
                     str(recording), str(freq)], text=True).strip()
                result = {'frequency_hz': freq, 'peak_dbfs': 20*math.log10(max(peak, 1)/32768),
                          'rms_dbfs': 20*math.log10(max(rms, 1)/32768),
                          'clipped_samples': sum(abs(v) >= 32760 for v in samples),
                          'analysis': analysis, 'recording': str(recording)}
                results.append(result)
                (out / f'{stem}-results.json').write_text(json.dumps(results, indent=2)+'\n')
                print(f"  peak {result['peak_dbfs']:.1f} dBFS; {analysis}", flush=True)
                if result['clipped_samples'] or result['peak_dbfs'] > -1:
                    raise RuntimeError('Microphone clipping/headroom problem; reduce input gain before continuing.')
                if rms < 2:
                    raise RuntimeError('Microphone recording is effectively silent; check hardware mute and placement.')
        if args.noise_baseline:
            baseline('quiet-test-gain-after')
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        errors = []
        restore = [('set-default-sink', state['default_sink'])]
        for kind, device in [('sink', sink), ('source', mic)]:
            restore.append((f'set-{kind}-volume', device['name'],
                            *(str(v['value']) for v in device['volume'].values())))
            restore.append((f'set-{kind}-mute', device['name'], str(int(device['mute']))))
        present = {s['index'] for s in devices('sink-inputs')}
        restore.extend(('set-sink-input-mute', str(s['index']), str(int(s['mute'])))
                       for s in streams if s['index'] in present)
        for command in restore:
            try:
                pactl(*command)
            except subprocess.CalledProcessError as e:
                errors.append(str(e))
        (out / f'{stem}-restore.json').write_text(json.dumps({'errors': errors}, indent=2)+'\n')
        print('Audio settings restored.' if not errors else f'Restore errors: {errors}', flush=True)


if __name__ == '__main__':
    main()
