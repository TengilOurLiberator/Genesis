import json
R = r"D:\genesis-vr\work\mcdata\out\reports"
c = json.load(open(R + r"\commands.json")); r = json.load(open(R + r"\registries.json"))
def show(node, name, depth, maxd):
    t = node.get("type"); p = node.get("parser", ""); ex = "*" if node.get("executable") else ""
    extra = json.dumps(node.get("properties")) if node.get("properties") else ""
    print("  " * depth + (f"<{name}:{p.replace('minecraft:','').replace('brigadier:','')}>" if t == "argument" else name) + ex + " " + extra)
    if depth < maxd:
        for k, v in node.get("children", {}).items(): show(v, k, depth + 1, maxd)
for cmd, d in [("posteffect", 5), ("spectate", 3), ("ride", 4), ("tick", 3), ("particle", 8), ("summon", 4), ("schedule", 5)]:
    show(c["children"][cmd], cmd, 0, d)
print("GAMERULES:", " ".join(sorted(k.replace("minecraft:", "") for k in r["minecraft:game_rule"]["entries"])))
print("ENVATTR:", " ".join(sorted(k.replace("minecraft:", "") for k in r["minecraft:environment_attribute"]["entries"])))
print("EFFECTS:", " ".join(sorted(k.replace("minecraft:", "") for k in r["minecraft:mob_effect"]["entries"])))
print("GENERATORS:", list(r["minecraft:worldgen/chunk_generator"]["entries"]))
