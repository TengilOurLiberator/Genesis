"""The companion (Eve or Adam): Claude plays the character, Chatterbox gives it a voice.

    uv run --project D:\\voice-assistant python companion.py --as eve --say "Who are you?" --out reply.wav
    uv run --project D:\\voice-assistant python companion.py --as eve          (type lines, hear replies)

The character comes from ..\\characters.md. The link to Minecraft and the microphone are added on top of this.
"""
import argparse, json, logging, os, re, subprocess, sys, wave

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
TALK_MODEL = "claude-haiku-5-5"   # quick enough for speech; sonnet takes about four seconds a reply


def character_sheet(who):
    """Who the companion is: the shared section and this character's own, taken from characters.md."""
    text = open(os.path.join(PROJECT, "characters.md"), encoding="utf-8").read()
    parts = {m.group(1).strip(): m.group(2).strip()
             for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M)}
    pick = lambda start: next(v for k, v in parts.items() if k.lower().startswith(start))
    other = "Adam" if who == "eve" else "Eve"
    return f"You are {who.capitalize()}. The only other person in the world is {other}.\n\n" + pick("shared") + "\n\n" + pick(who)


def character_prompt(who):
    """The sheet plus plain-speech rules, for talking to the companion outside the game."""
    return (character_sheet(who) + "\n\nEverything you write is spoken aloud, so write only the words you say: "
            "no stage directions, no asterisks, no brackets, no lists.")

class Brain:
    """One long-lived headless Claude Code process, one JSON line per turn, no tools."""

    def __init__(self, system_prompt, model=TALK_MODEL):
        exe = os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe")
        if not os.path.exists(exe):
            sys.exit("Claude Code is not installed at " + exe)
        self.proc = subprocess.Popen(
            [exe, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
             "--model", model, "--system-prompt", system_prompt,
             "--strict-mcp-config", "--mcp-config", json.dumps({"mcpServers": {}}), "--tools", ""],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1, cwd=os.path.expanduser("~"),
            env={**os.environ, "MAX_THINKING_TOKENS": "0"},
        )

    def ask(self, text):
        self.proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        self.proc.stdin.flush()
        for line in self.proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                return (event.get("result") or "").strip()
        return ""

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass


class Voice:
    def __init__(self, who):
        logging.getLogger("chatterbox").setLevel(logging.ERROR)
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        self.tts = ChatterboxTurboTTS.from_pretrained(device="cuda")
        # Eve speaks in the model's own built-in voice, which Willi found the most natural of three.
        # Adam still imitates a reference clip, because the model has no built-in man's voice.
        if who != "eve":
            self.tts.prepare_conditionals(os.path.join(PROJECT, "voices", f"{who}_ref.wav"))
        self.sr = self.tts.sr

    def synth(self, text):
        wav = self.tts.generate(text, temperature=0.8).squeeze().cpu().numpy().astype(np.float32)
        return wav / max(1e-6, float(np.abs(wav).max())) * 0.9

    def save(self, wav, path):
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sr)
            w.writeframes((np.clip(wav, -1, 1) * 32767).astype("<i2").tobytes())

    def play(self, wav):
        import sounddevice as sd

        sd.play(wav, self.sr)
        sd.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as", dest="who", choices=["eve", "adam"], default="eve", help="who the companion is")
    ap.add_argument("--say", help="one line from the player; reply once and exit")
    ap.add_argument("--out", help="with --say: write the spoken reply to this WAV instead of playing it")
    args = ap.parse_args()

    brain, voice = Brain(character_prompt(args.who)), Voice(args.who)
    try:
        if args.say:
            reply = brain.ask(args.say)
            print(f"{args.who.capitalize()}: {reply}")
            wav = voice.synth(reply)
            voice.save(wav, args.out) if args.out else voice.play(wav)
            return
        print(f"Talking with {args.who.capitalize()}. Type a line and press Enter; an empty line quits.")
        while True:
            said = input("> ").strip()
            if not said:
                break
            reply = brain.ask(said)
            print(f"{args.who.capitalize()}: {reply}")
            voice.play(voice.synth(reply))
    finally:
        brain.close()


if __name__ == "__main__":
    main()
