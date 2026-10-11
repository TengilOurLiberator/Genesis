import json, sys
R = r"D:\genesis-vr\work\mcdata\out\reports"
c = json.load(open(R + r"\commands.json"))
print("COMMANDS:", " ".join(sorted(c["children"])))
def show(node, name, depth, maxd):
    t = node.get("type"); p = node.get("parser", ""); ex = "*" if node.get("executable") else ""
    print("  " * depth + (f"<{name}:{p.replace('minecraft:','').replace('brigadier:','')}>" if t == "argument" else name) + ex)
    if depth < maxd:
        for k, v in node.get("children", {}).items(): show(v, k, depth + 1, maxd)
for cmd, d in [("time", 4), ("weather", 3), ("playsound", 9), ("place", 3), ("fillbiome", 6), ("rotate", 4), ("return", 2), ("waypoint", 2), ("stopwatch", 2), ("fetchprofile", 3)]:
    if cmd in c["children"]: show(c["children"][cmd], cmd, 0, d)
r = json.load(open(R + r"\registries.json"))
ent = sorted(k.replace("minecraft:", "") for k in r["minecraft:entity_type"]["entries"])
print("ENTITIES:", " ".join(ent))
print("PARTICLES:", " ".join(sorted(k.replace("minecraft:", "") for k in r["minecraft:particle_type"]["entries"])))
print("ATTRS:", " ".join(sorted(k.replace("minecraft:", "") for k in r["minecraft:attribute"]["entries"])))
print("REGS:", " ".join(sorted(k.replace("minecraft:", "") for k in r)))
