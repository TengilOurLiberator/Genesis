"""Assemble the narration from the best take of each verse.

Take 2 is the base. The verses listed in FROM_TAKE_1 are word-exact in take 1 and not in take 2, so they
are taken from take 1 and brought to take 2's level. Writes verses\\best.
"""
import glob, os, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROM_TAKE_1 = {"gen-1-12", "gen-1-21", "gen-1-22", "gen-1-31", "gen-2-01"}
SR = 48000


def load(path):
    with wave.open(path) as w:
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.uint8).reshape(-1, 3)
    i32 = raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int8).astype(np.int32) << 16)
    return i32.astype(np.float32) / 8388608


def save(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 8388607).astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


def level(x):
    hop = SR // 100
    d = 20 * np.log10(np.maximum(np.sqrt(np.mean(x[:len(x) // hop * hop].reshape(-1, hop) ** 2, axis=1)), 1e-7))
    return float(np.mean(d[d > -45]))


out = os.path.join(ROOT, "verses", "best")
os.makedirs(out, exist_ok=True)
take2 = {os.path.basename(p): load(p) for p in sorted(glob.glob(os.path.join(ROOT, "verses", "take2", "*.wav")))}
target = float(np.median([level(v) for k, v in take2.items() if k[3:-4] not in FROM_TAKE_1]))
for name, x in take2.items():
    if name[3:-4] in FROM_TAKE_1:
        y = load(os.path.join(ROOT, "verses", "dry", name))
        gain = min(target - level(y), -1.0 - 20 * np.log10(float(np.abs(y).max())))
        x = y * 10 ** (gain / 20)
        print(f"{name}: from take 1, {gain:+.1f} dB")
    save(os.path.join(out, name), x)
print(f"{len(take2)} verses written, take 2 speech level {target:.1f} dB")
