"""Apply the 'voice of God' sound to every verse clip and join them.

Reads verses\\dry\\*.wav, writes verses\\god\\*.wav (each with its own reverb tail)
and narration-godlike.wav. Speech timing inside a clip is unchanged.
"""
import glob, os, subprocess, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np

ROOT = r"D:\genesis-vr"
SR = 48000
TAIL = 6.0   # seconds of room left ringing after each verse
GAP = 2.0    # seconds between the end of one verse's speech and the next in the joined file
ir_path = os.path.join(ROOT, "work", "hall-ir.wav")


def save(path, x, ch):
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(3)
        w.setframerate(SR)
        i32 = (np.clip(x, -1, 1) * 8388607).astype("<i4")
        w.writeframes(i32.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


def load24(path, ch=2):
    raw = np.fromfile(path + ".raw", dtype=np.uint8).reshape(-1, 3)
    os.remove(path + ".raw")
    i32 = raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int8).astype(np.int32) << 16)
    return (i32.astype(np.float32) / 8388608).reshape(-1, ch)


# Impulse response of a vast space: decaying stereo noise, darker than white, no direct sound.
rng = np.random.default_rng(7)
n = int(SR * 6.5)
t = np.arange(n) / SR
f = np.fft.rfftfreq(n, 1 / SR)
shape = (1 / np.sqrt(1 + (f / 3000) ** 2)) * (f / np.sqrt(f ** 2 + 160 ** 2))
chans = []
for _ in range(2):
    h = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * shape, n) * np.exp(-6.91 * t / 5.0) * np.minimum(t / 0.03, 1.0)
    chans.append(h / np.sqrt(np.sum(h ** 2)))
ir = np.stack(chans, axis=1)
save(ir_path, ir / np.abs(ir).max() * 0.9, 2)

graph = (
    f"[0:a]highpass=f=70,apad=pad_dur={TAIL},asplit=4[a][b][c][d];"
    # the voice itself, about four semitones down, formants moving with it (a larger speaker)
    "[a]rubberband=pitch=0.80:pitchq=quality:formant=shifted[main];"
    # a second, slightly detuned and delayed copy: more than one voice speaking as one
    "[b]rubberband=pitch=0.788:pitchq=quality:formant=shifted,adelay=24:all=1,volume=-5dB[dbl];"
    # an octave below that, felt more than heard
    "[c]rubberband=pitch=0.40:pitchq=quality,lowpass=f=320,volume=-7dB[sub];"
    # a faint breath an octave above
    "[d]rubberband=pitch=1.60:pitchq=quality,highpass=f=1000,adelay=38:all=1,volume=-18dB[air];"
    "[main][dbl][sub][air]amix=inputs=4:normalize=0,"
    "acompressor=threshold=-22dB:ratio=3:attack=8:release=220:makeup=3,"
    "equalizer=f=100:t=q:w=0.8:g=4,equalizer=f=2800:t=q:w=1.2:g=3.5,"
    "aformat=channel_layouts=stereo,asplit=2[dry][send];"
    "[send]adelay=50:all=1[pre];"
    "[pre][1:a]afir=dry=0:wet=1:irnorm=-1[wet0];"
    "[wet0]volume=-9.5dB[wet];"
    "[dry][wet]amix=inputs=2:normalize=0,volume=-10dB,aresample=48000"
)

src_dir, out_dir = os.path.join(ROOT, "verses", "dry"), os.path.join(ROOT, "verses", "god")
os.makedirs(out_dir, exist_ok=True)
files = sorted(glob.glob(os.path.join(src_dir, "*.wav")))


def render(path):
    out = os.path.join(out_dir, os.path.basename(path))
    # raw samples: ffmpeg writes 24-bit stereo WAV with a header the wave module cannot read
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-i", ir_path, "-filter_complex", graph,
                        "-f", "s24le", "-ac", "2", out + ".raw"], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return out


with ThreadPoolExecutor(8) as ex:
    outs = list(ex.map(render, files))

# One gain for every clip, so verses keep their relative loudness.
clips = [load24(p) for p in outs]
peak = max(float(np.abs(c).max()) for c in clips)
gain = 10 ** (-1.5 / 20) / peak
print(f"peak before gain {20 * np.log10(peak):.1f} dB, uniform gain {20 * np.log10(gain):+.1f} dB")
starts, pos = [], 0.5
for p, c in zip(outs, clips):
    save(p, c * gain, 2)
    starts.append(pos)
    pos += len(c) / SR - TAIL + GAP
full = np.zeros((int((pos + TAIL) * SR), 2), np.float32)
for s, c in zip(starts, clips):
    a = int(s * SR)
    full[a:a + len(c)] += c * gain
full *= min(1.0, 10 ** (-1.0 / 20) / float(np.abs(full).max()))
save(os.path.join(ROOT, "narration-godlike.wav"), full, 2)
print(f"narration-godlike.wav  {len(full) / SR:.1f}s, {len(clips)} verses")

