"""Cut the narration into one clean clip per verse, splice in the retakes, and join them.

Writes verses\\dry\\NN_gen-C-VV.wav and narration-final.wav.
"""
import os, wave
import numpy as np

ROOT = r"D:\genesis-vr"
SR = 48000
GAP = 1.5  # seconds of silence between verses in the joined file


def load(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(axis=1)
    return x


def save(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        i32 = (np.clip(x, -1, 1) * 8388607).astype("<i4")
        w.writeframes(i32.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


def frame_db(x, hop=480):
    n = len(x) // hop
    r = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    return 20 * np.log10(np.maximum(r, 1e-7))


def snap(db, t, radius=0.9, win=0.2):
    """Centre of the quietest `win` seconds within `radius` of t (frames are 10 ms)."""
    lo, hi = max(0, int((t - radius) * 100)), min(len(db), int((t + radius) * 100))
    k = int(win * 100)
    sums = np.convolve(db[lo:hi], np.ones(k), mode="valid")
    return (lo + int(np.argmin(sums)) + k / 2) / 100


def trim(x, thresh=-45.0, lead=0.12, tail=0.30):
    db = frame_db(x)
    on = np.where(db > thresh)[0]
    a = max(0, int((on[0] / 100 - lead) * SR))
    b = min(len(x), int((on[-1] / 100 + 0.01 + tail) * SR))
    y = x[a:b].copy()
    f = int(0.02 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def active_db(x, thresh=-45.0):
    db = frame_db(x)
    return float(np.mean(db[db > thresh]))


def cut(x, labels, bounds):
    db = frame_db(x)
    cuts = [bounds[0]] + [snap(db, t) for t in bounds[1:-1]] + [bounds[-1]]
    out = {}
    for lab, a, b in zip(labels, cuts[:-1], cuts[1:]):
        if not lab.startswith("H"):
            out[lab] = trim(x[int(a * SR):int(b * SR)])
    return out


# Segment labels in spoken order (H = a day heading read aloud, dropped) and the
# approximate pause between each pair, refined by snap().
main_labels = ["H1", "1:1", "1:2", "1:3", "1:4", "1:5", "H2", "1:6", "1:7", "1:8", "H3", "1:9", "1:10",
               "1:11", "1:12", "1:13", "H4", "1:14", "1:15", "1:16", "1:17", "1:18", "1:19", "H5",
               "1:20", "1:21", "1:22", "1:23", "H6", "1:24", "1:25", "1:26", "1:27", "1:28", "1:29",
               "1:30", "1:31", "H7", "2:1", "2:2", "2:3"]
main_bounds = [2.0, 6.9, 12.1, 24.2, 31.3, 39.3, 50.0, 53.4, 62.5, 72.6, 81.4, 84.3, 93.9, 103.6,
               118.6, 132.6, 139.0, 142.5, 156.1, 164.7, 175.6, 181.0, 190.1, 195.2, 198.3,
               211.5, 226.4, 237.5, 241.4, 244.4, 257.8, 270.4, 288.9, 297.6, 315.9, 332.8,
               345.9, 356.9, 359.9, 364.6, 374.9, 386.5]
extra_labels = ["1:11", "1:12", "1:14", "1:15", "2:3"]
extra_bounds = [0.0, 14.1, 27.7, 40.6, 47.7, 58.4]

main = load(os.path.join(ROOT, "Genesis-1.1-2.wav"))
extra = load(os.path.join(ROOT, "extra_verses.wav"))
clips = cut(main, main_labels, main_bounds)
retakes = cut(extra, extra_labels, extra_bounds)

target = float(np.median([active_db(v) for k, v in clips.items() if k not in retakes]))
for lab, y in retakes.items():
    gain = float(np.clip(target - active_db(y), -9, 9))
    gain = min(gain, -1.0 - 20 * np.log10(np.abs(y).max()))  # keep peaks under -1 dB
    clips[lab] = y * 10 ** (gain / 20)
    print(f"retake {lab}: {len(y) / SR:5.1f}s, level matched by {gain:+.1f} dB")

order = [l for l in main_labels if not l.startswith("H")]
outdir = os.path.join(ROOT, "verses", "dry")
os.makedirs(outdir, exist_ok=True)
joined = [np.zeros(int(0.5 * SR), np.float32)]
for i, lab in enumerate(order, 1):
    c, v = lab.split(":")
    name = f"{i:02d}_gen-{c}-{int(v):02d}.wav"
    save(os.path.join(outdir, name), clips[lab])
    joined += [clips[lab], np.zeros(int(GAP * SR), np.float32)]
    print(f"{name}  {len(clips[lab]) / SR:5.1f}s  peak {20 * np.log10(np.abs(clips[lab]).max()):5.1f} dB")
full = np.concatenate(joined)
save(os.path.join(ROOT, "narration-final.wav"), full)
print(f"narration-final.wav  {len(full) / SR:.1f}s, {len(order)} verses")
