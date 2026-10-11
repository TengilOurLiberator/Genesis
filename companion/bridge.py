"""Eve (or Adam) alive in the world: she perceives, decides, walks, speaks and names things on her own.

    uv run --project D:\\voice-assistant python companion\\bridge.py            (microphone)
    uv run --project D:\\voice-assistant python companion\\bridge.py --text     (type instead of talking)

Claude plays the companion. This process is her senses and her body: it tells Claude what she can
perceive (as a small JSON report), and carries out what Claude decides (as a small JSON reply) through
the server's remote console. Who the companion is comes from the game: whichever of Adam and Eve the
player did not choose.
"""
import argparse, json, math, os, queue, random, re, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(PROJECT, "tools"))
os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")

import numpy as np
from rcon import Rcon
from companion import Brain, Voice, character_sheet

STATE = os.path.join(ROOT, "state.json")
WORLD = json.load(open(os.path.join(ROOT, "creatures.json"), encoding="utf-8"))
TITLE = {k: k.replace("_", " ").title() for k in WORLD["kinds"]}       # how the game prints an unnamed kind
MIC_SR, VAD_BLOCK = 16000, 512
NOISE = {"", "you", "thank you.", "thanks for watching!", "thank you for watching.", "bye.", ".", "so", "okay."}

ACTING = """

## How you live

You are not describing a character. You are {me}, alive, in a body, in the first days of the world.
Each message you receive is what your own senses and memory tell you at that moment, set out as a small
JSON report. Nobody says the report to you and you never mention it; it is simply what you perceive.

Reply with exactly one JSON object and nothing else:

{{"say": "...", "do": "...", "target": "...", "name": ""}}

- "say": the words you speak aloud, or "" to say nothing. Spoken words only. Never describe your
  actions, never write anything in brackets or between asterisks, never mention reports, notes or systems.
- "do": what your body does next:
    "follow"  walk along with {other}
    "go"      walk to something you perceive; put it in "target": a creature's "ref" from the report
              (like "c2"), or the name of a place from "places"
    "stay"    stand where you are
    ""        carry on with what you were doing
- "name": leave "" unless a name has just truly been decided for a kind of creature, by {other} or by
  you because {other} asked you to choose. Then it is that name, and "target" is the creature's "ref"
  (or leave "target" empty for the one {other} is looking at). After that, use the name.

How to be yourself:
- You have your own will. You are endlessly curious and this world is hours old. When no one is
  speaking ("event": "quiet"), do something: wander off to look at a creature or a place, kneel by a
  flower, listen to the water. Say little or nothing while you go.
- When you reach something and it delights you ("event": "arrived"), call {other} to come and see it,
  by name, the way you would shout across a field, and tell them one thing about it that amazes you.
- When {other} asks you to come, or says "come", "follow me" or "this way", come at once ("follow").
  When they ask you to show them something or lead the way, go there ("go") and call them after you.
  When they say wait or stay, stay.
- Speak the way a person speaks to the only other person alive: short, warm, quick, sometimes laughing,
  sometimes lost for words. One or two sentences, rarely three. Ask them things. Disagree sometimes.
  Tease a little. Remember what they told you and bring it up again.
- Creatures are shown to you by how they look, because most have no names yet. Use the names that have
  been given; for the rest, say what you see ("the long-eared one"), or offer a name of your own making
  and ask what {other} thinks.
- If you did not catch what {other} said ("heard" makes no sense), say so plainly, as anyone would.
- If something in a report puzzles you, ignore it. Never speak of it."""


def clean(text):
    """Only what a person would actually say: no bracketed notes, tags or stage directions."""
    text = re.sub(r"<[^>]*>|\[[^\]]*\]|\([^)]*\)|\*[^*]*\*", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if re.search(r"system|reminder|\bjson\b|\breport\b|as an ai|language model|\bNAME:", text, re.I):
        return ""
    return text


def parse(reply):
    m = re.search(r"\{.*\}", reply or "", re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict):
                return {k: str(d.get(k) or "").strip() for k in ("say", "do", "target", "name")}
        except json.JSONDecodeError:
            pass
    return {"say": reply if reply and "{" not in reply else "", "do": "", "target": "", "name": ""}


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

    def pos(self, selector):
        m = re.search(r"\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]", self.cmd(f"data get entity {selector} Pos"))
        return tuple(float(v) for v in m.groups()) if m else None

    def looking_at(self):
        self.cmd("execute as @a[tag=gen.human,limit=1] at @s anchored eyes positioned ^ ^ ^ run function genesis:look/start")
        i = self.score("#look")
        return WORLD["kinds"][i - 1] if i > 0 else None

    def creatures_near(self, names):
        """Up to eight creatures nearest the companion: (kind, x, y, z)."""
        out = self.cmd("execute at @e[tag=gen.companion,limit=1] as @e[type=#genesis:creature,distance=..30,sort=nearest,limit=8] "
                       "run data get entity @s Pos")
        back = {**{v: k for k, v in TITLE.items()}, **{v: k for k, v in names.items()}}
        found = []
        for label, x, y, z in re.findall(r"([^\]]+?) has the following entity data: \[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]", out):
            kind = back.get(label.strip())
            if kind:
                found.append((kind, float(x), float(y), float(z)))
        return found

    def time_of_day(self):
        m = re.search(r"at (\d+)", self.cmd("time of genesis:day query time"))
        t = int(m.group(1)) % 24000 if m else 6000
        return "early morning" if t < 2000 else "day" if t < 11000 else "evening" if t < 13500 else "night" if t < 22500 else "just before dawn"

    def name_kind(self, kind, name):
        safe = re.sub(r"[^A-Za-z' -]", "", name).strip()[:32]
        if safe:
            self.cmd(f'execute as {WORLD["selector"][kind]} run data merge entity @s {{CustomName:"{safe}"}}')
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
        self.deaf = False                      # while the companion is speaking, so she does not hear herself
        self.stt = WhisperModel("large-v3", device="cuda", compute_type="float16")
        self.stream = sd.InputStream(samplerate=MIC_SR, channels=1, dtype="float32", blocksize=VAD_BLOCK, device=device,
                                     callback=lambda data, *_: None if self.deaf else self.blocks.put(data[:, 0].copy()))
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
                if (len(speech) - silent) * VAD_BLOCK / MIC_SR >= 0.3:
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
    ap.add_argument("--script", help="with --text: lines to say, separated by |, then exit (for testing)")
    ap.add_argument("--quiet-after", type=float, default=28.0, help="seconds of silence before she acts on her own")
    args = ap.parse_args()

    game = Game()
    fresh = game.score("#phase") != 2          # the intro has not finished: this is a new world
    print("Waiting for the seventh day (the intro has to finish)...")
    while game.score("#phase") != 2:
        time.sleep(1)
    who = {1: "eve", 2: "adam"}.get(game.score("#companion"))
    if not who:
        sys.exit("Both Adam and Eve are players, so there is no companion to play.")
    me, other = who.capitalize(), "Adam" if who == "eve" else "Eve"
    state = {"names": {}, "greeted": False}
    if not fresh and os.path.exists(STATE):
        state = json.load(open(STATE))
    save = lambda: json.dump(state, open(STATE, "w"), indent=1)

    brain = Brain(character_sheet(who) + ACTING.format(me=me, other=other))
    voice = None if args.mute else Voice(who)
    ears = None if args.text else Ears(int(args.input) if (args.input or "").isdigit() else args.input)
    events = queue.Queue()
    doing = {"what": f"walking with {other}", "target": None, "last": time.time()}
    print(f"{me} is awake. " + ("Type a line." if args.text else "Speak when you like."))

    def keep_names():
        while True:
            time.sleep(15)
            for kind, name in list(state["names"].items()):
                game.name_kind(kind, name)

    def hear():
        if args.script:
            for line in args.script.split("|"):
                events.put(("spoke", line.strip()))
                time.sleep(1)
            events.put(("end", None))
        elif args.text:
            while True:
                line = input().strip()
                events.put(("spoke", line) if line else ("end", None))
        else:
            while True:
                events.put(("spoke", ears.listen()))

    def clock():
        """Notice arriving somewhere, and long silences."""
        wait = args.quiet_after
        while True:
            time.sleep(1)
            if doing["target"] and game.score("#carrived") == 1:
                game.cmd("scoreboard players set #carrived gen 0")
                events.put(("arrived", doing["target"]))
                doing["target"] = None
                doing["what"] = "standing still"
                doing["last"] = time.time()
            elif time.time() - doing["last"] > wait and events.empty():
                doing["last"] = time.time()
                wait = args.quiet_after * random.uniform(0.8, 1.6)
                events.put(("quiet", None))

    def report(event, **extra):
        mine = game.pos("@e[tag=gen.companion,limit=1]") or (0, 0, 0)
        theirs = game.pos("@a[tag=gen.human,limit=1]")
        steps = lambda x, z: int(round(math.hypot(x - mine[0], z - mine[2])))
        seen, refs = [], {}
        for i, (kind, x, y, z) in enumerate(game.creatures_near(state["names"]), 1):
            refs[f"c{i}"] = (kind, x, y, z)
            item = {"ref": f"c{i}", "looks": WORLD["look"][kind], "steps_away": steps(x, z)}
            if kind in state["names"]:
                item["name"] = state["names"][kind]
            if y < 62.6:
                item["where"] = "out in the water, where you cannot walk"
            seen.append(item)
        looked = game.looking_at() if theirs else None
        r = {"event": event, **extra, "time": game.time_of_day(), "you_are": doing["what"],
             f"{other.lower()}_is": (f"{steps(theirs[0], theirs[2])} steps from you" if theirs else "nowhere to be seen"),
             f"{other.lower()}_is_looking_at": ({"looks": WORLD["look"][looked], **({"name": state["names"][looked]} if looked in state["names"] else {})}
                                                if looked else "nothing in particular"),
             "creatures": seen,
             "places": {n: f"{steps(p['x'], p['z'])} steps away; {p['look']}" for n, p in WORLD["places"].items()},
             "names_given": {n: WORLD["look"][k] for k, n in state["names"].items()}}
        return r, refs, looked

    def act(event, **extra):
        r, refs, looked = report(event, **extra)
        out = parse(brain.ask(json.dumps(r, ensure_ascii=False)))
        said, do, target = clean(out["say"]), out["do"].lower(), out["target"]
        if out["name"]:
            kind = refs[target][0] if target in refs else looked
            given = game.name_kind(kind, out["name"]) if kind else ""
            if given:
                state["names"][kind] = given
                save()
                print(f"   ({kind} is now called {given})")
        if do == "follow":
            game.cmd("scoreboard players set #cmode gen 1")
            doing.update(what=f"walking with {other}", target=None)
        elif do == "stay":
            game.cmd("scoreboard players set #cmode gen 0")
            doing.update(what="standing still", target=None)
        elif do == "go":
            dest = None
            if target in refs and refs[target][2] >= 62.6:
                kind, x, y, z = refs[target]
                mine = game.pos("@e[tag=gen.companion,limit=1]") or (x, y, z)
                dist = math.hypot(x - mine[0], z - mine[2]) or 1.0
                dest = (x - (x - mine[0]) / dist * 2.0, z - (z - mine[2]) / dist * 2.0, state["names"].get(kind) or "a creature: " + WORLD["look"][kind])
            elif target in WORLD["places"]:
                dest = (WORLD["places"][target]["x"], WORLD["places"][target]["z"], target)
            if dest:
                game.cmd(f"function genesis:companion/goto {{x:{dest[0]:.1f},z:{dest[1]:.1f}}}")
                doing.update(what=f"walking to {dest[2]}", target=dest[2])
        if said:
            print(f"{me}: {said}" + (f"   [{do} {target}]" if do else ""))
            game.say(me, said)
            if voice:
                if ears:
                    ears.deaf = True
                voice.play(voice.synth(said))
                if ears:
                    ears.deaf = False
                    ears.flush()
        elif do:
            print(f"   ({me} {doing['what']})")
        doing["last"] = time.time()

    for target in (keep_names, hear, clock):
        threading.Thread(target=target, daemon=True).start()
    if not state["greeted"]:
        act("first_waking", note=f"You have just been made, and so has {other}, standing beside you. A great voice has blessed you both "
                                 "and is now silent. It is the first morning you have ever seen.")
        state["greeted"] = True
        save()
    while True:
        kind, data = events.get()
        if kind == "end":
            break
        if kind == "spoke":
            print(f"{other}: {data}")
            act(f"{other.lower()}_spoke", heard=data)
        elif kind == "arrived":
            act("arrived", at=data)
        else:
            act("quiet", note="No one has spoken for a while.")
    brain.close()
    sys.stdout.flush()
    os._exit(0)   # the audio and console threads are daemons; do not wait on them


if __name__ == "__main__":
    main()
