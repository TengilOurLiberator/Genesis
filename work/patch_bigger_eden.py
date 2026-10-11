"""One-off: move build_datapack.py to the larger Eden (lake, river, mountain, five kinds of country)."""
import re

P = r"D:\genesis-vr\tools\build_datapack.py"
s = open(P, encoding="utf-8").read()
count = 0


def rep(a, b, n=1):
    global s, count
    assert s.count(a) >= 1, "not found: " + a[:70]
    s = s.replace(a, b) if n == 0 else s.replace(a, b, n)
    count += 1


def block(start, end, new):
    global s, count
    i, j = s.index(start), s.index(end)
    assert i < j
    s = s[:i] + new + s[j:]
    count += 1


rep("CLEAR_Z = 30        # stage z of the clearing where they wake", "CLEAR_Z = 60        # stage z of the clearing where they wake")
rep("CAM0_S = (0.5, 66.0, 122.5)\n", "")
block("# ---------------------------------------------------------------- the island",
      "# ---------------------------------------------------------------- creatures",
      open(r"D:\genesis-vr\work\eden_terrain.py.txt", encoding="utf-8").read())

# counts: a bigger land holds more
for kind, old, new in [("cow", 6, 9), ("sheep", 8, 12), ("pig", 5, 7), ("horse", 5, 8), ("rabbit", 8, 12), ("frog", 5, 8),
                       ("turtle", 4, 6), ("bee", 6, 10), ("llama", 4, 6), ("panda", 3, 5), ("camel", 2, 4), ("armadillo", 4, 6)]:
    m = re.search(r'("%s": \(".*?", )%d(, ")' % (kind, old), s)
    assert m, kind
    s = s[:m.start()] + m.group(1) + str(new) + m.group(2) + s[m.end():]

block("hill = max(hmap, key=hmap.get)", 'json.dump({"kinds": KINDS,', '''cherries = [t for t in tree_sites if t[3] == "cherry"]
zone_centre = lambda name: tuple(int(v) for v in np.mean([(t[0], t[1]) for t in tree_sites if zone(t[0], t[1], t[2]) == name] or [(0, 0)], axis=0))


def place(name, x, z, look):
    wx, wz = wp(x + 0.5, z + 0.5)
    return name, {"x": round(wx, 1), "z": round(wz, 1), "look": look}


PLACES = dict([
    place("the lake", 0, LAKE_S + 2, "a wide still water in the middle of the land, ahead of where you woke; lilies float on it and reeds grow at its edge"),
    place("the falling stream", 6, LAKE[1] - 20, "where water comes down the face of the mountain and runs into the lake"),
    place("the river", 37, 30, "running water that leaves the lake and goes down to the great water"),
    place("the mountain", 30, MOUNT[1] + 22, "the great height beyond the lake, grey stone above the trees and white at the very top"),
    place("the near shore", 0, S0 - 4, "behind where you woke, where the land ends in pale sand and the great water begins"),
    place("the clearing", 0, CLEAR_Z + 2, "the flat ground where you both first opened your eyes"),
    place("the meadow", 0, CLEAR_Z - 26, "the wide open grass between the clearing and the lake, where the creatures graze"),
    place("the pink trees", *zone_centre("cherry"), "a grove to the left, every tree covered in pale pink blossom that drifts down"),
    place("the forest", *zone_centre("forest"), "tall green trees across the river, with flowers under them"),
    place("the jungle", *zone_centre("jungle"), "a thick tangle of huge trees and tall green canes, beyond the river and the lake"),
    place("the dry grassland", *zone_centre("savanna"), "open yellow-green ground with flat-topped trees, far to the left"),
])
''')
block("meadow = [c for c in open_cols if c not in plant_cols", "def summon(kind, x, y, z, extra", '''free = [c for c in open_cols if (c[0], c[1]) not in plant_cols]
meadow = [c for c in free if zone(*c) == "meadow" and 66 <= c[2] <= 73 and abs(c[0]) < 30 and LAKE_S + 3 < c[1] < CLEAR_Z - 6]
edges = [c for c in free if zone(*c) == "meadow" and c[2] <= 72 and 12 < abs(c[0]) < 30 and CLEAR_Z - 4 < c[1] < CLEAR_Z + 16] or meadow
lake_shore = [(x, z, SEA) for (x, z) in banks if abs(x) < 30 and z > LAKE[1] + 4 and lake_e[x + N, z + N] < 2.2] or meadow
nearest = lambda name: sorted([c for c in free if zone(*c) == name and c[2] < 90], key=lambda c: math.hypot(c[0], c[1] - 20))[:160] or meadow
POOL = {"frog": lake_shore, "turtle": lake_shore, "armadillo": nearest("savanna"), "camel": nearest("savanna"),
        "panda": nearest("jungle"), "llama": nearest("mountain")}
for pool in [meadow, edges, lake_shore] + list(POOL.values()):
    random.shuffle(pool)
_used = [0]


def spot(pool):
    _used[0] += 1
    x, z, h = pool[(_used[0] * 7) % len(pool)]
    return x + 0.5, h + 1, z + 0.5


''')
rep("z = 126 - 110 * k / max(1, (SPIRIT1 - SPIRIT0) // 2)", "z = S0 + 60 - 110 * k / max(1, (SPIRIT1 - SPIRIT0) // 2)")
rep("orb_at = pt(0.5, 82, 50)", "orb_at = pt(0.5, 86, S0 - 16)")
rep('"particle minecraft:bubble_pop 0 63 0 42 0.2 42 0.01 500 force"', '"particle minecraft:bubble_pop 0 63 0 62 0.2 62 0.01 800 force"')
rep('"particle minecraft:splash 0 63.2 0 40 0.3 40 0.2 400 force"', '"particle minecraft:splash 0 63.2 0 60 0.3 60 0.2 700 force"')
rep('"particle minecraft:splash 0 63.2 0 46 0.4 46 0.3 300 force"', '"particle minecraft:splash 0 63.2 0 68 0.4 68 0.3 500 force"')
rep('f"particle minecraft:cloud 0 {y} 0 30 0.5 30 0.02 50 force"', 'f"particle minecraft:cloud 0 {y} 0 45 0.5 45 0.02 80 force"')
rep('f"particle minecraft:dust_plume 0 {y} 0 26 0.4 26 0.02 40 force"', 'f"particle minecraft:dust_plume 0 {y} 0 40 0.4 40 0.02 60 force"')
rep("random.uniform(57, 61), random.uniform(78, 116))", "random.uniform(57, 61), random.uniform(S0 + 10, S0 + 48))")
rep("x, z = random.uniform(-14, 14), random.uniform(80, 90)", "x, z = random.uniform(-14, 14), random.uniform(S0 + 12, S0 + 22)")
rep("random.uniform(66, 76), random.uniform(68, 92))", "random.uniform(66, 78), random.uniform(S0 - 4, S0 + 20))")
rep('summon("dolphin", -12, 53, 80, whale(9.0))', 'summon("dolphin", -12, 54, S0 + 12, whale(9.0))')
rep('summon("dolphin", 15, 52, 76, whale(7.0))', 'summon("dolphin", 15, 53, S0 + 8, whale(7.0))')
rep("{pt(0.5, 54, 80)} 10 3 4 0.1 200 force", "{pt(0.5, 54, S0 + 12)} 10 3 4 0.1 200 force")
rep('summon("dolphin", random.uniform(-16, 16), 57, random.uniform(82, 100))', 'summon("dolphin", random.uniform(-16, 16), 57, random.uniform(S0 + 14, S0 + 32))')
rep("{pt(0.5, 69.5, 6)} 18 0.6 14 0 200 force", "{pt(0.5, 69.5, CLEAR_Z - 28)} 22 0.6 16 0 260 force")
rep("pt(a, random.uniform(120, 150), random.uniform(-40, 60))", "pt(a * 1.5, random.uniform(150, 190), random.uniform(-80, 80))")
rep('from_earth(kind, edges if kind in ("turtle", "frog") else meadow)', "from_earth(kind, POOL.get(kind, meadow))")
rep("FIRST = 12", "FIRST = 30")
rep('sound(SWIM, "minecraft:entity.dolphin.splash", 0.8, 0.8)', '''lake_water = [p for p in inland_water if lake_e[p[0] + N, p[1] + N] < 0.6]
for i in range(10):                                         # and the lake has its own
    x, z = random.choice(lake_water)
    at(SWIM + 20 + i * 5, [summon("salmon" if i % 2 else "cod", x + 0.5, 60.5, z + 0.5), f"particle minecraft:splash {pt(x + 0.5, 63.2, z + 0.5)} 0.3 0.1 0.3 0.1 10 force"])
sound(SWIM, "minecraft:entity.dolphin.splash", 0.8, 0.8)''')
rep('sound(tc(10, 1), "minecraft:ambient.underwater.exit", 0.7, 0.7)', '''sound(tc(10, 1), "minecraft:ambient.underwater.exit", 0.7, 0.7)
_sx, _sz = wb(SPRING[0], SPRING[2])                         # the spring on the mountain starts to run
at(tc(10, 1), [f"setblock {_sx} {SPRING[1]} {_sz} minecraft:water", f"particle minecraft:splash {_sx} {SPRING[1] + 1} {_sz} 0.5 0.5 0.5 0.2 60 force"])''')
block("cam_keys = [", "for (t0, p0), (t1, p1) in zip(cam_keys, cam_keys[1:]):", '''cam_keys = [(0, CAM0_S), (LIFT, CAM0_S), (E[7] + 30, (0.5, 74, S0 + 56.5)),
            (RISE2, (0.5, 74, S0 + 56.5)), (E[10], (0.5, 112, S0 + 78.5)),
            (S[11], (0.5, 112, S0 + 78.5)), (E[12] + 40, (0.5, 98, S0 + 42.5)),
            (S[20] - 30, (0.5, 98, S0 + 42.5)), (SWIM, (0.5, 64.3, S0 + 28.5)),
            (S[21] - 6, (0.5, 64.3, S0 + 28.5)), (WHALES - 4, (0.5, 55.5, S0 + 28.5)),
            (WINGED, (0.5, 55.5, S0 + 28.5)), (WINGED + 50, (0.5, 64.3, S0 + 28.5)),
            (S[22], (0.5, 64.3, S0 + 28.5)), (E[22], (0.5, 72, S0 + 28.5)),
            (S[23], (0.5, 72, S0 + 28.5)), (tw(24, "the living creature"), (0.5, 86, cz + 38)),
            (S[25], (0.5, 86, cz + 38)), (E[25], (0.5, 78, cz + 26)),
            (S[26] - 20, (0.5, 78, cz + 26)), (BEAM + 30, (0.5, 69.4, cz + 12)),
            (E[27] + 14, (0.5, 69.4, cz + 12)), (AWAKE, (0.5, 69.0, cz + 1.0))]
''')
rep('"forceload add -144 -96 95 95", ', '"forceload add -192 -136 -65 135", "forceload add -64 -136 39 135", "forceload add 40 -136 135 135", ')
rep(f'f"schedule function {{NS}}:setup2 60t"])', f'f"schedule function {{NS}}:setup2 60t", f"schedule function {{NS}}:setup3 120t"])\nfn("setup3", BIOMES)   # the different kinds of country, laid over the sea before any land exists')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("patched", count, "places")
