#!/usr/bin/env python3
"""Report the level of each probe tone in a capture (leakage-free Goertzel)."""
import math, os, struct, sys, wave
FS=48000; WINDOW=48000
CACHE=os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),"omarchy-audio-tuner")
FREQ_LIST=os.path.join(CACHE,"dense-freqs.txt")
if not os.path.exists(FREQ_LIST):
    sys.exit(f"No tone list at {FREQ_LIST}. Run: omarchy-audio-tuner probe")
freqs=[int(l) for l in open(FREQ_LIST)]
with wave.open(sys.argv[1],"rb") as w:
    ch=w.getnchannels(); raw=w.readframes(w.getnframes())
d=struct.unpack("<%dh"%(len(raw)//2),raw)
if ch>1: d=[sum(d[i:i+ch])/ch for i in range(0,len(d),ch)]
start=int(0.3*FS); seg=list(d[start:start+WINDOW])
if len(seg)<WINDOW: seg=list(d[:WINDOW])
out=[]
for f in freqs:
    k=round(f*WINDOW/FS); w0=2*math.pi*k/WINDOW; c=2*math.cos(w0)
    s1=s2=0.0
    for s in seg:
        s0=s+c*s1-s2; s2,s1=s1,s0
    a=2*math.hypot(s1-s2*math.cos(w0), s2*math.sin(w0))/WINDOW
    out.append(f"{f} {20*math.log10(a/32768) if a>0 else -999:.2f}")
print("\n".join(out))
