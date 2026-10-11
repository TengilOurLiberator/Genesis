"""Use Willi's own reading as the narration: copy the verse clips and find when each clause is spoken.

Reads verses\\dry\\NN_gen-C-VV.wav (cut by work\\build_verses.py), writes narration\\dry\\vNN.wav and
narration\\timing.json in the same form make_narration.py produces, so the game can time things to the words.
"""
import difflib, glob, json, os, re, subprocess

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import torch

os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "narration", "dry")
os.makedirs(OUT, exist_ok=True)

verses = []
for line in open(os.path.join(ROOT, "narration-script.md"), encoding="utf-8"):
    m = re.match(r"\*\*(\d+):(\d+)\*\*\s+(.*)", line.strip())
    if m:
        verses.append((f"{m.group(1)}:{m.group(2)}", m.group(3)))


def clauses(text):
    """Split at the King James punctuation (: ; .), and long clauses again at a comma near the middle."""
    parts = [p.strip() for p in re.split(r"(?<=[:;.])\s+", text) if p.strip()]
    out = []
    for p in parts:
        if len(p) > 150:
            commas = [m.end() for m in re.finditer(r",\s", p)]
            if commas:
                cut = min(commas, key=lambda c: abs(c - len(p) / 2))
                out += [p[:cut].strip(), p[cut:].strip()]
                continue
        out.append(p)
    return out


norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
stt = WhisperModel("large-v3", device="cuda", compute_type="float16")
timing, differs = {}, []
files = sorted(glob.glob(os.path.join(ROOT, "verses", "best", "*.wav")))   # see work\best_of_takes.py
for i, ((ref, text), path) in enumerate(zip(verses, files), 1):
    dst = os.path.join(OUT, f"v{i:02d}.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", dst], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                               capture_output=True, text=True).stdout)
    segs, _ = stt.transcribe(dst, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False, vad_filter=True,
                             no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None, temperature=0.0)
    heard = [(norm(w.word), w.start, w.end) for s in segs for w in s.words if norm(w.word)]
    cl = clauses(text)
    want = [(norm(w), j) for j, c in enumerate(cl) for w in c.replace("every thing", "everything").split() if norm(w)]
    sm = difflib.SequenceMatcher(None, [w for w, _ in want], [w for w, _, _ in heard], autojunk=False)
    when = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            when[a + k] = (heard[b + k][1], heard[b + k][2])
    if sm.ratio() < 1.0:
        differs.append(f"{ref}: " + "; ".join(f"{' '.join(w for w, _ in want[a:b]) or '-'} -> {' '.join(w for w, _, _ in heard[c:d]) or '-'}"
                                             for op, a, b, c, d in sm.get_opcodes() if op != "equal"))
    marks, last_end = [], 0.0
    for j, c in enumerate(cl):
        idx = [k for k, (_, cj) in enumerate(want) if cj == j and k in when]
        start = when[idx[0]][0] if idx else last_end
        end = when[idx[-1]][1] if idx else min(dur, start + 1.0)
        start = max(start, last_end)
        marks.append({"text": c, "start": round(start, 3), "end": round(max(end, start + 0.2), 3)})
        last_end = marks[-1]["end"]
    timing[i] = {"ref": ref, "duration": round(dur, 3), "clauses": marks}
    print(f"v{i:02d} {ref}: {dur:5.1f}s  " + " | ".join(f"{m['start']:.1f}-{m['end']:.1f}" for m in marks), flush=True)
json.dump(timing, open(os.path.join(ROOT, "narration", "timing.json"), "w"), indent=1)
print("total speech", round(sum(t["duration"] for t in timing.values()), 1), "s")
print("verses where the reading differs from the text (or was misheard):", len(differs))
for d in differs:
    print("  ", d)
