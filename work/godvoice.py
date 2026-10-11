"""Give the narration a large, deep, reverberant 'voice from above' sound.

usage: godvoice.py <in.wav> <out.wav>
Timing is preserved, so verse cut points found on the input stay valid on the output.
"""
import subprocess, sys, wave
import numpy as np

src, out = sys.argv[1], sys.argv[2]
ir_path = r"D:\genesis-vr\work\hall-ir.wav"
SR = 48000

# Impulse response of a very large hall: decaying stereo noise, darker than white, no direct sound.
rng = np.random.default_rng(7)
n = int(SR * 5.5)
t = np.arange(n) / SR
f = np.fft.rfftfreq(n, 1 / SR)
shape = (1 / np.sqrt(1 + (f / 3500) ** 2)) * (f / np.sqrt(f ** 2 + 180 ** 2))
chans = []
for _ in range(2):
    noise = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * shape, n)
    env = np.exp(-6.91 * t / 4.2) * np.minimum(t / 0.03, 1.0)
    h = noise * env
    chans.append(h / np.sqrt(np.sum(h ** 2)))
ir = np.stack(chans, axis=1)
with wave.open(ir_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(3)
    w.setframerate(SR)
    i32 = (np.clip(ir / np.abs(ir).max() * 0.9, -1, 1) * 8388607).astype("<i4")
    w.writeframes(i32.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())

graph = (
    "[0:a]highpass=f=70,asplit=2[a][b];"
    # main voice two semitones down, formants moving with it so the speaker sounds larger
    "[a]rubberband=pitch=0.891:pitchq=quality:formant=shifted[main];"
    # an octave-down shadow underneath
    "[b]rubberband=pitch=0.5:pitchq=quality,lowpass=f=260,volume=-12dB[sub];"
    "[main][sub]amix=inputs=2:normalize=0,"
    "acompressor=threshold=-22dB:ratio=3:attack=8:release=220:makeup=3,"
    "equalizer=f=110:t=q:w=0.8:g=3,equalizer=f=3200:t=q:w=1.2:g=2,"
    "aformat=channel_layouts=stereo,asplit=2[dry][send];"
    "[send]adelay=45:all=1[pre];"
    "[pre][1:a]afir=dry=0:wet=1:irnorm=-1[wet0];"
    "[wet0]volume=-11dB[wet];"
    "[dry][wet]amix=inputs=2:normalize=0,"
    "loudnorm=I=-18:TP=-1.5:LRA=11,alimiter=limit=0.89,aresample=48000"
)
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-i", ir_path, "-filter_complex", graph,
       "-c:a", "pcm_s24le", out]
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stderr.strip() or "ok")
sys.exit(r.returncode)
