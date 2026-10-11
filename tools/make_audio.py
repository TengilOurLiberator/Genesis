"""Generate the score and the sound effects with the local models (ACE-Step 1.5 and Stable Audio Open,
through ComfyUI), finish them, and put them in the resource pack.

Music lengths come from work\\schedule.json, so run build_datapack.py first.
    python tools\\make_audio.py [--only music|sfx] [--names deep,light]
"""
import argparse, json, os, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = r"D:\godtree-tools\ComfyUI_windows_portable"
SERVER = "http://127.0.0.1:8188"
SOUNDS = os.path.join(ROOT, "pack", "genesis-resources", "assets", "genesis", "sounds")
RAW = os.path.join(ROOT, "work", "audio")

ACE = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ace_step_1.5_turbo_aio.safetensors"}},
       "2": {"class_type": "TextEncodeAceStepAudio1.5", "inputs": {
           "clip": ["1", 1], "tags": "", "lyrics": "[Instrumental]", "seed": 0, "bpm": 60, "duration": 30.0,
           "timesignature": "4", "language": "en", "keyscale": "C major", "generate_audio_codes": True,
           "cfg_scale": 2.0, "temperature": 0.85, "top_p": 0.9, "top_k": 0, "min_p": 0.0}},
       "3": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["2", 0]}},
       "4": {"class_type": "EmptyAceStep1.5LatentAudio", "inputs": {"seconds": 30.0, "batch_size": 1}},
       "5": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
       "6": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
                                                  "seed": 0, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
       "7": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
       "8": {"class_type": "SaveAudio", "inputs": {"audio": ["7", 0], "filename_prefix": "genesis"}}}
SAO = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
       "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5_base.safetensors", "type": "stable_audio", "device": "default"}},
       "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
       "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": "music, melody, speech, voice, low quality, hiss, noise, distortion"}},
       "5": {"class_type": "ConditioningStableAudio", "inputs": {"positive": ["3", 0], "negative": ["4", 0], "seconds_start": 0.0, "seconds_total": 10.0}},
       "6": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": 10.0, "batch_size": 1}},
       "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "latent_image": ["6", 0],
                                                  "seed": 0, "steps": 60, "cfg": 6.0, "sampler_name": "dpmpp_3m_sde_gpu", "scheduler": "exponential", "denoise": 1.0}},
       "8": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
       "9": {"class_type": "SaveAudio", "inputs": {"audio": ["8", 0], "filename_prefix": "genesis"}}}

STYLE = "instrumental, cinematic film score, orchestral, reverent, spacious, no vocals, no lyrics, "
MUSIC = {  # name: (tags, bpm, key)
    "deep": ("dark ambient drone, deep sub bass, distant low choir hum, vast empty void, slowly evolving pad, ominous and holy, no drums, no melody", 50, "D minor"),
    "light": ("radiant choir aahs swelling, shimmering high strings, harp glissando, awe and wonder, first sunrise, bright major chords, no drums", 60, "D major"),
    "firmament": ("airy glassy pads, soft high strings, gentle wind chimes, weightless, floating, calm, wide open sky, no drums", 60, "A major"),
    "earth": ("deep cellos and french horns rising, timpani rolls, a great slow build, then pastoral flutes and harp, growth and green life", 70, "G major"),
    "heavens": ("majestic celestial theme, full choir aahs, soaring strings, celesta and glockenspiel sparkles, grand crescendo, wonder at the stars", 66, "E major"),
    "waters": ("flowing harp arpeggios, playful flute and clarinet, gentle marimba, oceanic, joyful, light and quick", 84, "F major"),
    "beasts": ("warm pastoral theme, lively strings, oboe melody, soft hand drums, earthy and noble, herds on open grassland", 90, "C major"),
    "man": ("tender solo cello and piano, intimate and still, slowly building to a full warm orchestra and choir, profound, the most moving moment", 60, "D major"),
    "rest": ("peaceful resolution, soft strings and distant choir, slow gentle harp, serene, a day of rest, fading into quiet", 54, "D major"),
}
SFX = {  # name: (prompt, seconds)
    "deep": ("deep underwater rumble in a vast dark ocean, low frequency drone, slow heavy water movement", 20),
    "wind": ("soft wind passing across open water, airy whoosh, gentle and wide", 12),
    "light": ("bright cinematic impact with a shimmering rising whoosh, sparkling glassy burst, radiant swell", 8),
    "rise": ("massive earthquake rumble, rock grinding, a huge landmass rising out of the sea, cascading water, deep bass", 18),
    "growth": ("leaves rustling, plants sprouting quickly, soft creaking wood, gentle natural growth", 10),
    "sun": ("glorious warm rising swell, deep resonant hum building upward, radiant cinematic riser", 9),
    "stars": ("delicate twinkling chimes, tiny glass bells, sparkling high shimmer, magical", 9),
    "whale": ("humpback whale song underwater, deep long calls, ocean ambience", 14),
    "birds": ("many birds singing, dawn chorus, wings fluttering, a lively flock taking flight", 14),
    "heartbeat": ("slow deep heartbeat, soft and close, warm low thump", 10),
    "bell": ("a single deep resonant temple bell strike with a long decay, low bronze bell", 10),
}


def api(path, body=None):
    req = urllib.request.Request(SERVER + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def start_comfy():
    try:
        api("/system_stats")
        return None
    except Exception:
        pass
    log = open(os.path.join(RAW, "comfy.log"), "w")
    proc = subprocess.Popen([os.path.join(COMFY, "python_embeded", "python.exe"), "-s", r"ComfyUI\main.py", "--windows-standalone-build",
                             "--disable-auto-launch", "--listen", "127.0.0.1", "--port", "8188",
                             "--extra-model-paths-config", r"D:\godtree-tools\extra_model_paths.yaml"],
                            cwd=COMFY, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(120):
        time.sleep(2)
        try:
            api("/system_stats")
            return proc
        except Exception:
            if proc.poll() is not None:
                sys.exit("ComfyUI stopped while starting; see work\\audio\\comfy.log")
    sys.exit("ComfyUI did not come up")


def run(workflow, prefix):
    saver = next(n for n in workflow.values() if n["class_type"] == "SaveAudio")
    saver["inputs"]["filename_prefix"] = "genesis/" + prefix
    pid = api("/prompt", {"prompt": workflow})["prompt_id"]
    for _ in range(600):
        time.sleep(1)
        hist = api(f"/history/{pid}")
        if pid in hist:
            status = hist[pid].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status)[:600])
            for out in hist[pid].get("outputs", {}).values():
                for a in out.get("audio", []):
                    return os.path.join(COMFY, "ComfyUI", "output", a.get("subfolder", ""), a["filename"])
    raise TimeoutError(prefix)


def finish(src, dst, seconds, lufs, fade_in, fade_out):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    af = (f"atrim=0:{seconds},loudnorm=I={lufs}:TP=-1.5:LRA=11,afade=t=in:d={fade_in},"
          f"afade=t=out:st={max(0.1, seconds - fade_out):.2f}:d={fade_out},aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ac", "2", "-c:a", "libvorbis", "-q:a", "6", dst], check=True)
    info = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", dst, "-af", "volumedetect", "-f", "null", "NUL"],
                          capture_output=True, text=True).stderr
    mean = next((l.split("mean_volume:")[1].strip() for l in info.splitlines() if "mean_volume" in l), "?")
    return mean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["music", "sfx"])
    ap.add_argument("--names", default="")
    args = ap.parse_args()
    names = set(filter(None, args.names.split(",")))
    os.makedirs(RAW, exist_ok=True)
    sections = {s["name"]: s["seconds"] for s in json.load(open(os.path.join(ROOT, "work", "schedule.json")))["music"]}
    proc = start_comfy()
    try:
        if args.only != "sfx":
            for i, (name, (tags, bpm, key)) in enumerate(MUSIC.items()):
                if names and name not in names:
                    continue
                seconds = round(min(240.0, sections.get(name, 40.0) + 5.0), 1)   # runs on under the next piece as it fades
                wf = json.loads(json.dumps(ACE))
                wf["2"]["inputs"].update({"tags": STYLE + tags, "bpm": bpm, "keyscale": key, "duration": seconds, "seed": 4100 + i})
                wf["4"]["inputs"]["seconds"] = seconds
                wf["6"]["inputs"]["seed"] = 4100 + i
                t0 = time.time()
                src = run(wf, "music_" + name)
                mean = finish(src, os.path.join(SOUNDS, "music", name + ".ogg"), seconds, -19, 2.0, 5.0)
                print(f"music {name}: {seconds}s, mean {mean}, {time.time() - t0:.0f}s to make", flush=True)
        if args.only != "music":
            for i, (name, (prompt, seconds)) in enumerate(SFX.items()):
                if names and name not in names:
                    continue
                wf = json.loads(json.dumps(SAO))
                wf["3"]["inputs"]["text"] = prompt
                wf["5"]["inputs"]["seconds_total"] = float(seconds)
                wf["6"]["inputs"]["seconds"] = float(seconds)
                wf["7"]["inputs"]["seed"] = 7300 + i
                t0 = time.time()
                src = run(wf, "sfx_" + name)
                mean = finish(src, os.path.join(SOUNDS, "sfx", name + ".ogg"), seconds, -17, 0.05, 1.5)
                print(f"sfx {name}: {seconds}s, mean {mean}, {time.time() - t0:.0f}s to make", flush=True)
    finally:
        if proc:
            proc.terminate()
    # the sound list for the resource pack: narration, music, effects
    entries = {}
    for kind, stream in (("god", True), ("music", True), ("sfx", False)):
        folder = os.path.join(SOUNDS, kind)
        for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if f.endswith(".ogg"):
                key = ("narration.god." if kind == "god" else kind + ".") + f[:-4]
                entries[key] = {"sounds": [{"name": f"genesis:{kind}/{f[:-4]}", "stream": stream}]}
    json.dump(entries, open(os.path.join(os.path.dirname(SOUNDS), "sounds.json"), "w"), indent=1)
    print("sounds.json:", len(entries), "entries")


if __name__ == "__main__":
    main()
