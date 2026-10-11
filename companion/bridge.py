"""Eve (or Adam) in the world: listens to the player, answers aloud, and gives the animals their names.

    uv run --project D:\\voice-assistant python companion\\bridge.py            (microphone)
    uv run --project D:\\voice-assistant python companion\\bridge.py --text     (type instead of talking)

Talks to the local server over its remote console. Who the companion is comes from the game:
it is whichever of Adam and Eve the player did not choose.
"""
import argparse, json, os, queue, re, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(PROJECT, "tools"))
os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")

import numpy as np
from rcon import Rcon
from companion import Brain, Voice, character_prompt

STATE = os.path.join(ROOT, "state.json")
CREATURES = json.load(open(os.path.join(ROOT, "creatures.json"), encoding="utf-8"))
MIC_SR, VAD_BLOCK = 16000, 512
NOISE = {"", "you", "thank you.", "thanks for watching!", "thank you for watching.", "bye.", "."}

NAMING = """

## Naming the creatures

Before each thing your companion says you are told, in square brackets, what they are looking at and
which kinds of creature already have names. Those notes are for you alone; never read them out.
Creatures are described, not named: you have no words for them until one of you gives one.
When your companion clearly chooses a name for the kind of creature they are looking at, accept it
gladly and end your reply with one extra line, exactly:
NAME: <the name>
Do the same if they ask you to choose and you choose. Do not add that line when you are only
suggesting or wondering, and never for a kind that is not being looked at. From then on use the name."""


def score(r, name):
    out = r.cmd(f"scoreboard players get {name} gen")
    m = re.search(r"has (-?\d+)", out)
    return int(m.group(1)) if m else 0


class Game:
    def __init__(self):
        self.r, self.lock = Rcon(), threading.Lock()

    def cmd(self, c):
        with self.lock:
            try:
                return self.r.cmd(c)
            except OSError:
                self.r = Rcon()
                return self.r.cmd(c)

    def score(self, name):
        m = re.search(r"has (-?\d+)", self.cmd(f"scoreboard players get {name} gen"))
        return int(m.group(1)) if m else 0

    def looking_at(self):
        self.cmd("execute as @a[tag=gen.human,limit=1] at @s anchored eyes positioned ^ ^ ^ run function genesis:look/start")
        i = self.score("#look")
        return CREATURES["kinds"][i - 1] if i > 0 else None

    def time_of_day(self):
        m = re.search(r"at (\d+)", self.cmd("time of genesis:day query time"))
        t = int(m.group(1)) % 24000 if m else 6000
        return "early morning" if t < 2000 else "day" if t < 11000 else "evening" if t < 13500 else "night" if t < 22500 else "just before dawn"

    def name_kind(self, kind, name):
        safe = re.sub(r"[^A-Za-z' -]", "", name).strip()[:32]
        if safe:
            self.cmd(f'execute as {CREATURES["selector"][kind]} run data merge entity @s {{CustomName:"{safe}"}}')
        return safe

    def say(self, who, text):
        self.cmd("tellraw @a " + json.dumps({"text": f"<{who}> {text}", "color": "aqua" if who == "Eve" else "gold"}, ensure_ascii=False))
        self.cmd("execute at @e[tag=gen.companion,limit=1] run particle minecraft:note ~ ~2.3 ~ 0.2 0.1 0.2 1 3 force")


class Ears:
    """Microphone -> one utterance at a time (Silero VAD) -> text (Whisper)."""

    def __init__(self, device=None, silence_s=0.8, threshold=0.5):
        import sounddevice as sd
        import torch
        from silero_vad import load_silero_vad

        os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
        os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ["PATH"]
        from faster_whisper import WhisperModel

        self.torch, self.vad, self.threshold = torch, load_silero_vad(), threshold
        self.silence_blocks = int(silence_s / (VAD_BLOCK / MIC_SR))
        self.blocks = queue.Queue()
        self.stt = WhisperModel("large-v3", device="cuda", compute_type="float16")
        self.stream = sd.InputStream(samplerate=MIC_SR, channels=1, dtype="float32", blocksize=VAD_BLOCK, device=device,
                                     callback=lambda data, *_: self.blocks.put(data[:, 0].copy()))
        self.stream.start()

    def flush(self):
        while not self.blocks.empty():
            self.blocks.get_nowait()
        self.vad.reset_states()

    def listen(self):
        pre, speech, silent, speaking = [], [], 0, False
        while True:
            block = self.blocks.get()
            prob = self.vad(self.torch.from_numpy(block), MIC_SR).item()
            if not speaking:
                pre = (pre + [block])[-10:]
                if prob >= self.threshold:
                    speaking, speech, silent = True, list(pre), 0
                continue
            speech.append(block)
            silent = 0 if prob >= self.threshold else silent + 1
            if silent >= self.silence_blocks:
                self.vad.reset_states()
                if (len(speech) - silent) * VAD_BLOCK / MIC_SR < 0.3:
                    pre, speech, silent, speaking = [], [], 0, False
                    continue
                segs, _ = self.stt.transcribe(np.concatenate(speech), language="en", beam_size=3,
                                              condition_on_previous_text=False)
                text = " ".join(s.text.strip() for s in segs).strip()
                if text.lower() not in NOISE:
                    return text
                pre, speech, silent, speaking = [], [], 0, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", action="store_true", help="type what the player says instead of using the microphone")
    ap.add_argument("--mute", action="store_true", help="do not speak aloud (replies still show in the game chat)")
    ap.add_argument("--input", help="microphone device name or index (default: the system default)")
    ap.add_argument("--once", help="with --text: say this one line, print the reply, and exit")
    args = ap.parse_args()

    game = Game()
    print("Waiting for the seventh day (the intro has to finish)...")
    while game.score("#phase") != 2:
        time.sleep(1)
    who = {1: "eve", 2: "adam"}.get(game.score("#companion"))
    if not who:
        sys.exit("Both Adam and Eve are players, so there is no companion to play.")
    player = "Adam" if who == "eve" else "Eve"
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"names": {}, "greeted": False}
    save = lambda: json.dump(state, open(STATE, "w"), indent=1)

    brain = Brain(character_prompt(who) + NAMING)
    voice = None if args.mute else Voice(who)
    ears = None if args.text else Ears(args.input if not (args.input or "").isdigit() else int(args.input))
    print(f"{who.capitalize()} is awake. " + ("Type a line." if args.text else "Speak when you like."))

    def keep_names():
        while True:
            time.sleep(15)
            for kind, name in list(state["names"].items()):
                game.name_kind(kind, name)
    threading.Thread(target=keep_names, daemon=True).start()

    def turn(note, said=None):
        reply = brain.ask(f"[{note}]" + (f'\n{player} says: "{said}"' if said else ""))
        m = re.search(r"^\s*NAME:\s*(.+?)\s*$", reply, re.M)
        spoken = re.sub(r"^\s*NAME:.*$", "", reply, flags=re.M).strip()
        if m and turn.kind:
            given = game.name_kind(turn.kind, m.group(1))
            if given:
                state["names"][turn.kind] = given
                save()
                print(f"   ({turn.kind} is now called {given})")
        print(f"{who.capitalize()}: {spoken}")
        game.say(who.capitalize(), spoken)
        if voice and spoken:
            voice.play(voice.synth(spoken))
        if ears:
            ears.flush()
        return spoken
    turn.kind = None

    if not state["greeted"]:
        turn(f"You have both just been made and have heard the blessing. It is {game.time_of_day()} on the seventh day. "
             f"The voice has fallen silent. Speak first to {player}: a few words of wonder, then ask what they see.")
        state["greeted"] = True
        save()

    while True:
        said = args.once or (input("> ").strip() if args.text else ears.listen())
        if not said:
            break
        print(f"{player}: {said}")
        kind = turn.kind = game.looking_at()
        names = ", ".join(f"{n} ({CREATURES['look'][k]})" for k, n in state["names"].items()) or "none yet"
        if kind:
            have = state["names"].get(kind)
            seen = f"{player} is looking at a creature: {CREATURES['look'][kind]}. " + (
                f"It is one of the kind you have named {have}." if have else "Its kind has no name yet.")
        else:
            seen = f"{player} is not looking at any creature in particular."
        turn(f"It is {game.time_of_day()}. {seen} Names given so far: {names}.", said)
        if args.once:
            break
    brain.close()
    os._exit(0)   # the audio and console threads are daemons; do not wait on them


if __name__ == "__main__":
    main()
