#!/usr/bin/env python3
"""Select the G14 EQ only for audio already targeting the internal device."""
import json
import subprocess
import sys
import time

HARDWARE = 'alsa_output.pci-0000_77_00.6.analog-stereo'
EQ = 'g14_speaker_eq'


def pactl(*args):
    return subprocess.check_output(['pactl', *args], text=True).strip()


def items(kind):
    return json.loads(pactl('-f', 'json', 'list', kind))


def main():
    if sys.argv[1:] == ['--bypass']:
        sinks = {s['name']: s for s in items('sinks')}
        if EQ not in sinks or HARDWARE not in sinks:
            return
        if pactl('get-default-sink') == EQ:
            pactl('set-default-sink', HARDWARE)
        for stream in items('sink-inputs'):
            if stream['sink'] == sinks[EQ]['index']:
                subprocess.run(['pactl', 'move-sink-input', str(stream['index']), HARDWARE],
                               check=False)
        return
    for _ in range(50):
        sinks = {s['name']: s for s in items('sinks')}
        if HARDWARE in sinks and EQ in sinks:
            hardware_id = sinks[HARDWARE]['index']
            outputs = [s for s in items('sink-inputs')
                       if s.get('properties', {}).get('node.name') == EQ + '_output']
            if outputs and all(s['sink'] == hardware_id for s in outputs):
                break
        time.sleep(0.2)
    else:
        raise SystemExit('EQ did not connect to the G14 internal audio device.')

    # Preserve another selected output (USB headphones, HDMI, Bluetooth).
    default = pactl('get-default-sink')
    if default == HARDWARE:
        pactl('set-default-sink', EQ)
    for stream in items('sink-inputs'):
        properties = stream.get('properties', {})
        if (stream['sink'] == hardware_id
                and properties.get('application.name')
                and properties.get('node.name') != EQ + '_output'):
            subprocess.run(['pactl', 'move-sink-input', str(stream['index']), EQ],
                           check=False)
    print('G14 EQ connected to internal audio; other outputs left unchanged.')


if __name__ == '__main__':
    main()
