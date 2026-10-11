"""Generate the narration: every verse of narration-script.md spoken by a synthetic voice, clause by clause.

Each clause is generated on its own, checked word for word against the text with Whisper, and
regenerated until it matches. Clause start times are written to narration\\timing.json so the game can
make things happen on the words that call for them.
"""
import difflib, json, logging, os, re, subprocess, sys, wave

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import numpy as np
import torch

os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
logging.getLogger("chatterbox").setLevel(logging.ERROR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "narration", "dry")
REF = r"D:\voice-assistant\voices\audition\english_default.wav"
SR = 48000
TRIES = 7
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


norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("every thing", "everything")).split()

import chatterbox.models.s3gen.flow_matching as flow_matching

flow_matching.print = lambda *a, **k: None
from chatterbox.tts import ChatterboxTTS
from faster_whisper import WhisperModel

tts = ChatterboxTTS.from_pretrained(device="cuda")
tts.prepare_conditionals(REF, exaggeration=0.45)
stt = WhisperModel("large-v3", device="cuda", compute_type="float16")


def resample(x, sr_from, sr_to):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr_from), "-ac", "1", "-i", "-",
                        "-ar", str(sr_to), "-f", "f32le", "-"], input=x.astype("<f4").tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, dtype="<f4")


def trim(x, sr, pad=0.06):
    hop = sr // 100
    n = len(x) // hop
    db = 20 * np.log10(np.maximum(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)), 1e-7))
    on = np.where(db > -42)[0]
    if not len(on):
        return x
    return x[max(0, int((on[0] / 100 - pad) * sr)):min(len(x), int((on[-1] / 100 + 0.01 + pad) * sr))]


def speak(text):
    best = None
    for attempt in range(TRIES):
        wav = tts.generate(text, exaggeration=0.45, cfg_weight=0.3, temperature=0.7).squeeze().cpu().numpy().astype(np.float32)
        wav = trim(wav, tts.sr)
        heard = " ".join(s.text for s in stt.transcribe(resample(wav, tts.sr, 16000), language="en", beam_size=5,
                                                        condition_on_previous_text=False)[0])
        score = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
        # a clause that drags or races is as wrong as a misread word
        rate = len(wav) / tts.sr / max(1, len(text.split()))
        if not 0.22 <= rate <= 0.62:
            score -= 0.2
        if best is None or score > best[0]:
            best = (score, wav, heard)
        if score == 1.0:
            break
    return best


timing, report = {}, []
for i, (ref, text) in enumerate(verses, 1):
    parts, pos, marks = [], 0.0, []
    cl = clauses(text)
    for j, c in enumerate(cl):
        score, wav, heard = speak(c)
        wav = resample(wav, tts.sr, SR)
        wav = wav / max(1e-6, float(np.abs(wav).max())) * 0.7
        marks.append({"text": c, "start": round(pos, 3), "end": round(pos + len(wav) / SR, 3)})
        parts.append(wav)
        pos += len(wav) / SR
        if j < len(cl) - 1:
            gap = 0.7 if c.endswith(".") else 0.5
            parts.append(np.zeros(int(gap * SR), np.float32))
            pos += gap
        if score < 1.0:
            report.append(f"{ref} [{score:.2f}] wanted: {c} | heard: {heard.strip()}")
    audio = np.concatenate(parts)
    with wave.open(os.path.join(OUT, f"v{i:02d}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    timing[i] = {"ref": ref, "duration": round(len(audio) / SR, 3), "clauses": marks}
    print(f"v{i:02d} {ref}: {len(audio) / SR:5.1f}s, {len(cl)} clauses", flush=True)
json.dump(timing, open(os.path.join(ROOT, "narration", "timing.json"), "w"), indent=1)
print("total speech", round(sum(t["duration"] for t in timing.values()), 1), "s")
print("clauses not word-perfect:", len(report))
for r in report:
    print("  ", r)
