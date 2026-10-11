"""Review a full narration take: levels, pauses, and how each verse compares with the script.

    python work\\review_take.py <take.wav>
Writes work\\take_words.json (every word with its time) for cutting afterwards.
"""
import difflib, json, os, re, subprocess, sys

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import numpy as np
import torch

os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
                       "-of", "default=nw=1"], capture_output=False, text=True, args=None) if False else None
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
                      "-of", "default=nw=1", src], capture_output=True, text=True).stdout.replace("\n", "  "))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype="<f4")
db = lambda v: 20 * np.log10(max(float(v), 1e-9))
hop = 160
fr = np.sqrt(np.mean(x[:len(x) // hop * hop].reshape(-1, hop) ** 2, axis=1))
fdb = 20 * np.log10(np.maximum(fr, 1e-7))
print(f"peak {db(np.abs(x).max()):.1f} dB | speech level {np.mean(fdb[fdb > -45]):.1f} dB | noise floor {np.percentile(fdb, 5):.1f} dB | "
      f"samples at full scale {int((np.abs(x) >= 0.999).sum())}")

verses = []
for line in open(os.path.join(ROOT, "narration-script.md"), encoding="utf-8"):
    m = re.match(r"\*\*(\d+):(\d+)\*\*\s+(.*)", line.strip())
    if m:
        verses.append((f"{m.group(1)}:{m.group(2)}", m.group(3)))
norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
stt = WhisperModel("large-v3", device="cuda", compute_type="float16")
segs, _ = stt.transcribe(x, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False,
                         vad_filter=True, no_speech_threshold=None, log_prob_threshold=None,
                         compression_ratio_threshold=None, temperature=0.0)
heard = [(norm(w.word), round(w.start, 2), round(w.end, 2)) for s in segs for w in s.words if norm(w.word)]
json.dump(heard, open(os.path.join(ROOT, "work", "take_words.json"), "w"))
want = [(norm(w), i) for i, (_, t) in enumerate(verses) for w in t.replace("every thing", "everything").split() if norm(w)]
sm = difflib.SequenceMatcher(None, [w for w, _ in want], [w for w, _, _ in heard], autojunk=False)
when, issues = {}, {}
for op, a, b, c, d in sm.get_opcodes():
    if op == "equal":
        for k in range(b - a):
            when[a + k] = heard[c + k]
    else:
        v = want[min(a, len(want) - 1)][1]
        issues.setdefault(v, []).append(f"{' '.join(w for w, _ in want[a:b]) or '-'} -> {' '.join(w for w, _, _ in heard[c:d]) or '-'}"
                                        + (f" (at {heard[c][1]:.0f}s)" if c < len(heard) else ""))
print(f"words heard {len(heard)}, script words {len(want)}, match {sm.ratio():.3f}")
prev_end = 0.0
for i, (ref, _) in enumerate(verses):
    idx = [k for k, (_, v) in enumerate(want) if v == i and k in when]
    if not idx:
        print(f"{ref:5} NOT FOUND")
        continue
    s, e = when[idx[0]][1], when[idx[-1]][2]
    print(f"{ref:5} {s:6.1f}-{e:6.1f}  pause before {s - prev_end:4.1f}s  " + ("; ".join(issues.get(i, [])) or "ok"))
    prev_end = e
