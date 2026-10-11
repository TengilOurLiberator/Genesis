import json, sys
v = sys.argv[1]
d = json.load(open(v + r"\timeline\day.json"))
print("day keys:", {k: (v2 if not isinstance(v2, (dict, list)) else type(v2).__name__) for k, v2 in d.items()})
for name, tr in d["tracks"].items():
    s = json.dumps(tr)
    print(name, "=>", s[:420])
print("MOON:", json.dumps(json.load(open(v + r"\timeline\moon.json")))[:700])
print("EARLY:", json.dumps(json.load(open(v + r"\timeline\early_game.json"))))
print("CLOCK:", [ (f, open(v + "\\world_clock\\" + f).read()) for f in __import__("os").listdir(v + r"\world_clock")])
print("TAG:", open(v + r"\tags\timeline\in_overworld.json").read())
# fog examples in biomes
import os
seen = {}
for f in os.listdir(v + r"\worldgen\biome"):
    b = json.load(open(v + "\\worldgen\\biome\\" + f))
    for k, val in b.get("attributes", {}).items():
        seen.setdefault(k, (f, val))
for k, (f, val) in seen.items():
    print(k, "@", f, "=", json.dumps(val)[:200])
print("PLAINS effects:", json.dumps(json.load(open(v + r"\worldgen\biome\plains.json"))["effects"]))
print("FLAT PRESET:", open(v + r"\worldgen\flat_level_generator_preset\water_world.json").read())
