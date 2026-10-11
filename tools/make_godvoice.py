"""Turn the generated narration into the voice heard in the game: slow, deep, many-voiced, and not human.

Reads narration\\dry\\vNN.wav, writes narration\\god\\vNN.wav and the Ogg files in the resource pack.
Every clip starts with PRE seconds of rising swell before the first word, and speech is slowed to
TEMPO of its generated speed; build_datapack.py relies on both numbers.
"""
import glob, json, os, subprocess, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
TEMPO = 1.0     # the recorded reading keeps its own pace
PRE = 1.2
TAIL = 7.0
ir_path = os.path.join(ROOT, "work", "hall-ir.wav")
src_dir, out_dir = os.path.join(ROOT, "narration", "dry"), os.path.join(ROOT, "narration", "god")
ogg_dir = os.path.join(ROOT, "pack", "genesis-resources", "assets", "genesis", "sounds", "god")
for p in (out_dir, ogg_dir, os.path.dirname(ir_path)):
    os.makedirs(p, exist_ok=True)


def save(path, x, ch):
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(3)
        w.setframerate(SR)
        i32 = (np.clip(x, -1, 1) * 8388607).astype("<i4")
        w.writeframes(i32.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


# Impulse response of a space with no walls you could name: six seconds of darkening stereo noise.
rng = np.random.default_rng(7)
n = int(SR * 7.0)
t = np.arange(n) / SR
f = np.fft.rfftfreq(n, 1 / SR)
shape = (1 / np.sqrt(1 + (f / 3200) ** 2)) * (f / np.sqrt(f ** 2 + 170 ** 2))
chans = []
for _ in range(2):
    h = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * shape, n) * np.exp(-6.91 * t / 5.6) * np.minimum(t / 0.03, 1.0)
    chans.append(h / np.sqrt(np.sum(h ** 2)))
ir = np.stack(chans, axis=1)
save(ir_path, ir / np.abs(ir).max() * 0.9, 2)

rb = lambda pitch, extra="": f"rubberband=tempo={TEMPO}:pitch={pitch}:pitchq=quality{extra}"
graph = (
    # the lead-in and tail are slowed along with the speech, so they are shortened here to come out right
    f"[0:a]highpass=f=70,adelay={int(PRE * TEMPO * 1000)}:all=1,apad=pad_dur={TAIL * TEMPO},asplit=4[a][b][c][d];"
    # the voice itself, three semitones down and larger; this is nearly all of what is heard directly
    f"[a]{rb(0.84, ':formant=shifted')}[main];"
    # a faint second speaker a hair lower and later
    f"[b]{rb(0.83, ':formant=shifted')},adelay=24:all=1,volume=-10dB[dbl];"
    # an octave beneath, felt more than heard
    f"[c]{rb(0.42)},lowpass=f=220,volume=-10dB[sub];"
    # an octave above. It is never heard directly, only in the echo, so it reads as a high company
    # answering from far off and not as a second, artificial voice
    f"[d]{rb(1.68, ':formant=preserved')},highpass=f=500,lowpass=f=7000,volume=-5dB,aformat=channel_layouts=stereo[halo];"
    "[main][dbl][sub]amix=inputs=3:normalize=0,"
    "acompressor=threshold=-22dB:ratio=2.5:attack=10:release=250:makeup=3,"
    "equalizer=f=100:t=q:w=0.8:g=3,equalizer=f=3000:t=q:w=1.2:g=2.5,"
    "aformat=channel_layouts=stereo,asplit=3[dry][send][rev];"
    "[send][halo]amix=inputs=2:normalize=0,adelay=50:all=1[pre];"
    "[pre][1:a]afir=dry=0:wet=1:irnorm=-1,volume=-9dB[wet];"
    # the echo that comes before the word: the same reverb, run backwards in time
    "[rev]areverse[r1];[r1][1:a]afir=dry=0:wet=1:irnorm=-1[r2];[r2]areverse,lowpass=f=4000,volume=-17dB[swell];"
    "[dry][wet][swell]amix=inputs=3:normalize=0,volume=-10dB,aresample=48000"
)
files = sorted(glob.glob(os.path.join(src_dir, "v*.wav")))


def render(path):
    out = os.path.join(out_dir, os.path.basename(path)) + ".raw"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-i", ir_path, "-filter_complex", graph,
                        "-f", "s24le", "-ac", "2", out], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    raw = np.fromfile(out, dtype=np.uint8).reshape(-1, 3)
    os.remove(out)
    i32 = raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int8).astype(np.int32) << 16)
    return (i32.astype(np.float32) / 8388608).reshape(-1, 2)


with ThreadPoolExecutor(8) as ex:
    clips = list(ex.map(render, files))
peak = max(float(np.abs(c).max()) for c in clips)
gain = 10 ** (-1.5 / 20) / peak                      # one gain for all, so verses keep their relative level
for path, c in zip(files, clips):
    name = os.path.basename(path)
    wav = os.path.join(out_dir, name)
    save(wav, c * gain, 2)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "6",
                    os.path.join(ogg_dir, name.replace(".wav", ".ogg"))], check=True)
total = sum(len(c) / SR - TAIL - PRE for c in clips)
json.dump({"stretch": 1 / TEMPO, "pre": PRE}, open(os.path.join(ROOT, "narration", "meta.json"), "w"))
print(f"{len(clips)} verses, speech {total:.1f}s at tempo {TEMPO}, uniform gain {20 * np.log10(gain):+.1f} dB")
