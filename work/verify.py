"""Transcribe every clip in a folder and compare it with the script, verse by verse."""
import difflib, glob, os, re, sys

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import torch

os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

folder = sys.argv[1]
script = {}
for line in open(r"D:\genesis-vr\narration-script.md", encoding="utf-8"):
    m = re.match(r"\*\*(\d+):(\d+)\*\*\s+(.*)", line.strip())
    if m:
        script[f"gen-{m.group(1)}-{int(m.group(2)):02d}"] = m.group(3)
norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("every thing", "everything")).split()

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
scores = []
for path in sorted(glob.glob(os.path.join(folder, "*.wav"))):
    key = os.path.basename(path)[3:-4]
    segs, _ = model.transcribe(path, language="en", beam_size=5, condition_on_previous_text=False,
                               no_speech_threshold=None, log_prob_threshold=None,
                               compression_ratio_threshold=None, temperature=0.0)
    heard, want = norm(" ".join(s.text for s in segs)), norm(script[key])
    sm = difflib.SequenceMatcher(None, want, heard)
    scores.append(sm.ratio())
    diffs = [f"{' '.join(want[a:b]) or '-'} -> {' '.join(heard[c:d]) or '-'}"
             for op, a, b, c, d in sm.get_opcodes() if op != "equal"]
    print(f"{key}  {sm.ratio():.2f}  {'; '.join(diffs)}")
print(f"mean {sum(scores) / len(scores):.3f}  clips {len(scores)}  exact {sum(s == 1 for s in scores)}")
