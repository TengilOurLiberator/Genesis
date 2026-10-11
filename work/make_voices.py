"""Build the reference clips for Eve's and Adam's voices and speak a sample line with each.

Both references are synthetic voices (Chatterbox's own sample voices), not recordings of a person.
"""
import os, subprocess, sys, wave

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import logging
import numpy as np

logging.getLogger("chatterbox").setLevel(logging.ERROR)
sys.path.insert(0, os.path.dirname(__file__))
from f0 import median_f0

ROOT = r"D:\genesis-vr\voices"
SRC = r"D:\voice-assistant\voices\audition"
os.makedirs(ROOT, exist_ok=True)

refs = {
    "eve": (os.path.join(SRC, "english_resemble_f1.wav"), None),
    # the male sample voice, lowered a little so Adam is clearly a man but not as deep as the narrator
    "adam": (os.path.join(SRC, "english_default.wav"), "rubberband=pitch=0.88:pitchq=quality:formant=shifted"),
}
lines = {
    "eve": "I woke, and the light was already here. Look, that one with the long neck is drinking. "
           "What shall we call it?",
    "adam": "The ground is warm under my hands. I walked to the river and back. "
            "Come, I will show you what I found.",
}

from chatterbox.tts_turbo import ChatterboxTurboTTS

tts = ChatterboxTurboTTS.from_pretrained(device="cuda")
for who, (src, fx) in refs.items():
    ref = os.path.join(ROOT, f"{who}_ref.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src] + (["-af", fx] if fx else []) + ["-ac", "1", ref], check=True)
    tts.prepare_conditionals(ref)
    wav = tts.generate(lines[who], temperature=0.8).squeeze().cpu().numpy().astype(np.float32)
    out = os.path.join(ROOT, f"{who}_sample.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tts.sr)
        w.writeframes((np.clip(wav / max(1e-6, np.abs(wav).max()) * 0.9, -1, 1) * 32767).astype("<i2").tobytes())
    f, d = median_f0(out)
    print(f"{who}: reference {median_f0(ref)[0]:.0f} Hz, sample {f:.0f} Hz, {d:.1f}s -> {out}")
