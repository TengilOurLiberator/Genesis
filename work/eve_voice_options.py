"""Speak one line three ways so Willi can pick the most natural voice for Eve."""
import logging, os, wave

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import numpy as np

logging.getLogger("chatterbox").setLevel(logging.ERROR)
OUT = r"D:\genesis-vr\voices\options"
os.makedirs(OUT, exist_ok=True)
LINE = ("Adam! Come quickly, come and see! There is a little one here with long ears, "
        "and it is not afraid of me at all. Oh, it is so soft.")
V = r"D:\voice-assistant\voices"


def save(name, wav, sr):
    wav = wav.squeeze().cpu().numpy().astype(np.float32)
    wav = wav / max(1e-6, float(np.abs(wav).max())) * 0.9
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((wav * 32767).astype("<i2").tobytes())
    print("wrote", name, round(len(wav) / sr, 1), "s", flush=True)


import chatterbox.models.s3gen.flow_matching as flow_matching

flow_matching.print = lambda *a, **k: None
from chatterbox.tts import ChatterboxTTS

full = ChatterboxTTS.from_pretrained(device="cuda")
for name, ref, ex, cfg in (("eve_A_expressive", os.path.join(V, "refs", "resemble_f1.wav"), 0.7, 0.45),
                           ("eve_B_calm", os.path.join(V, "audition", "english_resemble_f1.wav"), 0.5, 0.5)):
    try:
        save(name, full.generate(LINE, audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=0.8), full.sr)
    except Exception as e:
        print(name, "failed:", e)
del full
from chatterbox.tts_turbo import ChatterboxTurboTTS

turbo = ChatterboxTurboTTS.from_pretrained(device="cuda")
save("eve_C_builtin", turbo.generate(LINE, temperature=0.8), turbo.sr)
