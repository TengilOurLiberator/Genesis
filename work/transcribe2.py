"""Transcribe the narration with word timestamps and save them as JSON."""
import json, os, sys

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import torch

# CTranslate2 needs the cuDNN/cuBLAS DLLs that ship inside the torch wheel.
os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
try:
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
except Exception as e:
    print("cuda failed, using cpu:", e)
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    src, language="en", word_timestamps=True, beam_size=5,
    condition_on_previous_text=False, vad_filter=True, no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None, temperature=0.0,
)
words = []
for s in segments:
    print(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}")
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
with open(out, "w", encoding="utf-8") as f:
    json.dump(words, f)
print("words:", len(words), "duration:", info.duration)

