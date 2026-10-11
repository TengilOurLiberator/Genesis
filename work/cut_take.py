"""Cut a full narration take into one clip per verse.

    python work\\cut_take.py <take.wav> <out_dir>

The take is transcribed in short overlapping pieces (one long pass skips stretches), the words are lined
up with the script, and each cut is made at the quietest moment between two verses.
"""
import difflib, os, re, subprocess, sys, wave

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import numpy as np
import torch

os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-af", "pan=mono|c0=c0", "-f", "f32le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, dtype="<f4")
x16 = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-ar", "16000",
                                    "-f", "f32le", "-"], input=raw, capture_output=True).stdout, dtype="<f4")
norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
verses = []
for line in open(os.path.join(ROOT, "narration-script.md"), encoding="utf-8"):
    m = re.match(r"\*\*(\d+):(\d+)\*\*\s+(.*)", line.strip())
    if m:
        verses.append((m.group(1), int(m.group(2)), m.group(3)))

stt = WhisperModel("large-v3", device="cuda", compute_type="float16")
WIN, STEP = 24.0, 16.0
words, t0 = [], 0.0
while t0 < len(x16) / 16000:
    piece = x16[int(t0 * 16000):int((t0 + WIN) * 16000)]
    segs, _ = stt.transcribe(piece, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False,
                             no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None, temperature=0.0)
    for s in segs:
        for w in s.words:
            mid = t0 + (w.start + w.end) / 2
            # keep each word from the window whose middle it is nearest, so overlaps are not doubled
            if norm(w.word) and (t0 == 0 or mid >= t0 + (WIN - STEP) / 2) and mid < t0 + STEP + (WIN - STEP) / 2:
                words.append((norm(w.word), t0 + w.start, t0 + w.end))
    t0 += STEP
words.sort(key=lambda w: w[1])
want = [(norm(w), i) for i, (_, _, t) in enumerate(verses) for w in t.replace("every thing", "everything").split() if norm(w)]
sm = difflib.SequenceMatcher(None, [w for w, _ in want], [w for w, _, _ in words], autojunk=False)
when = {}
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        when[a + k] = words[b + k]
print(f"words heard {len(words)}, script words {len(want)}, match {sm.ratio():.3f}")
spans = []
for i in range(len(verses)):
    idx = [k for k, (_, v) in enumerate(want) if v == i and k in when]
    if not idx:
        sys.exit(f"verse {verses[i][0]}:{verses[i][1]} was not found in the take")
    spans.append((when[idx[0]][1], when[idx[-1]][2], when[idx[0]], when[idx[-1]]))

hop = SR // 200                                    # 5 ms frames
fr = np.sqrt(np.mean(x[:len(x) // hop * hop].reshape(-1, hop) ** 2, axis=1))
fdb = 20 * np.log10(np.maximum(fr, 1e-7))


def quietest(last, first, win=0.08):
    """Between the middle of one verse's last word and the middle of the next verse's first word."""
    a, b = (last[1] + last[2]) / 2, (first[1] + first[2]) / 2
    if b - a < 0.2:
        a, b = a - 0.1, b + 0.1
    lo, hi, k = int(a * 200), max(int(a * 200) + 17, int(b * 200)), int(win * 200)
    sums = np.convolve(fdb[lo:hi], np.ones(k), mode="valid")
    return (lo + int(np.argmin(sums)) + k / 2) / 200


cuts = [max(0.0, spans[0][0] - 0.6)] + [quietest(spans[i][3], spans[i + 1][2]) for i in range(len(spans) - 1)] + [min(len(x) / SR, spans[-1][1] + 0.8)]
for i, (c, v, _) in enumerate(verses):
    y = x[int(cuts[i] * SR):int(cuts[i + 1] * SR)]
    d = 20 * np.log10(np.maximum(np.sqrt(np.mean(y[:len(y) // hop * hop].reshape(-1, hop) ** 2, axis=1)), 1e-7))
    on = np.where(d > -45)[0]
    a, b = max(0, int((on[0] / 200 - 0.10) * SR)), min(len(y), int((on[-1] / 200 + 0.30) * SR))
    y = y[a:b].copy()
    f = min(int(0.015 * SR), len(y) // 4)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    with wave.open(os.path.join(out_dir, f"{i + 1:02d}_gen-{c}-{v:02d}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 8388607).astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes())
    gap = spans[i + 1][0] - spans[i][1] if i + 1 < len(spans) else 0
    print(f"{c}:{v:<3} {cuts[i]:6.1f}-{cuts[i + 1]:6.1f}  {len(y) / SR:5.1f}s  gap after {gap:4.2f}s")
