"""Generate the Genesis datapack: the island, the sky script and the timed intro.

    python tools\\build_datapack.py

Reads narration\\timing.json (when each clause of each verse is spoken) and the vanilla day timeline from
work\\mcdata (made with the server jar's data generator). Writes datapack\\genesis, companion\\creatures.json
and work\\schedule.json. Things happen on the words that call for them: see `tw()`.
"""
import json, math, os, random, shutil
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "datapack", "genesis")
VANILLA = os.path.join(ROOT, "work", "mcdata", "vanilla", "data", "minecraft")
NS = "genesis"
random.seed(31)

SEA = 62            # top water block
FLOOR = 42          # top of the sea bed
LOBBY = (1000, 100, 1000)
_meta = json.load(open(os.path.join(ROOT, "narration", "meta.json")))   # written by make_godvoice.py
STRETCH = _meta["stretch"]  # how much the voice was slowed
PRE = _meta["pre"]          # seconds of swell at the start of every narration clip before the first word
CLEAR_Z = 60        # stage z of the clearing where they wake

# Everything is laid out on a "stage" with the viewer to the south looking north. The stage is then
# turned a quarter so that the viewer looks east: the first sunrise comes up straight ahead, behind
# the hill, and it does so again on the seventh morning for the man and the woman.
wp = lambda x, z: (-z, x)                      # stage point -> world point
wb = lambda x, z: (-z - 1, x)                  # stage block -> world block
yaw = lambda stage: (stage + 90 + 180) % 360 - 180
FACE = yaw(180)                                # the direction everything happens in (east)


def fill(x1, z1, x2, z2, y, rest):
    return f"fill {-z2 - 1} {y} {x1} {-z1 - 1} {y} {x2} {rest}"


def pt(x, y, z):
    wx, wz = wp(x, z)
    return f"{wx:.2f} {y:.2f} {wz:.2f}"


ADAM_S, EVE_S = (-1.5, CLEAR_Z + 0.5), (2.5, CLEAR_Z + 0.5)
ADAM, EVE = pt(ADAM_S[0], 69, ADAM_S[1]), pt(EVE_S[0], 69, EVE_S[1])

# ---------------------------------------------------------------- files
funcs = {}


def fn(name, lines):
    funcs.setdefault(name, []).extend(lines if isinstance(lines, list) else [lines])


def write(rel, data):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data if isinstance(data, str) else json.dumps(data, indent=1))


# ---------------------------------------------------------------- the island
# Eden: an island about two hundred blocks across. The clearing where they wake is near the south
# shore; ahead of it lie a meadow, then a lake at sea level, then a mountain with a stream running down
# into the lake. A river leaves the lake and winds to the sea on the right. Around these are a cherry
# grove (left), a forest beyond the river (right), a dry grassland (far left) and a jungle (far right).
N = 132
xs = np.arange(-N, N + 1)
X, Z = np.meshgrid(xs, xs, indexing="ij")
R = np.hypot(X, Z)
TH = np.arctan2(Z, X)
RC = 100
coast = RC + 10 * np.sin(3 * TH + 1.0) + 6 * np.sin(5 * TH + 2.2) + 3.5 * np.sin(9 * TH + 0.4)
d = 1 - R / coast                                   # 0 at the shore, 1 at the centre
S0 = int(RC + 10 * math.sin(3 * math.pi / 2 + 1.0) + 6 * math.sin(5 * math.pi / 2 + 2.2) + 3.5 * math.sin(9 * math.pi / 2 + 0.4))  # the near shore


def smooth(a):
    a = np.clip(a, 0, 1)
    return a * a * (3 - 2 * a)


def value_noise(scale, seed):
    g = np.random.default_rng(seed).random((2 * N // scale + 3, 2 * N // scale + 3))
    fx, fz = (X + N) / scale, (Z + N) / scale
    ix, iz = fx.astype(int), fz.astype(int)
    tx, tz = smooth(fx - ix), smooth(fz - iz)
    return (g[ix, iz] * (1 - tx) + g[ix + 1, iz] * tx) * (1 - tz) + (g[ix, iz + 1] * (1 - tx) + g[ix + 1, iz + 1] * tx) * tz


bump = lambda cx, cz, amp, sig: amp * np.exp(-((X - cx) ** 2 + (Z - cz) ** 2) / (2 * sig ** 2))
MOUNT = (0, -64)
land = 1.2 + 2.3 * smooth(d / 0.10) + 4.6 * smooth((d - 0.08) / 0.6)
mountain = bump(MOUNT[0], MOUNT[1], 56, 19) + bump(-30, -52, 30, 13) + bump(28, -56, 22, 12)
land += mountain * (0.85 + 0.3 * value_noise(9, 11))
land += bump(-64, 8, 10, 16) + bump(62, 12, 9, 15)                       # low rises to the left and right
land += (value_noise(14, 5) - 0.5) * 2.6 * smooth(d / 0.2)
height = np.where(d > 0, SEA + land, SEA + d * 170.0)
clearing = smooth((17 - np.hypot(X, Z - CLEAR_Z)) / 8)                    # flat ground where they wake
height = height * (1 - clearing) + 68.0 * clearing

# the lake: a hollow at sea level, so that when the land rises the water is simply left there
LAKE = (0, -14)
lake_e = (X / 27.0) ** 2 + ((Z - LAKE[1]) / 16.0) ** 2 + 0.3 * (value_noise(10, 21) - 0.5)
height = np.where(lake_e < 1, 59.6 - 3.0 * smooth((1 - lake_e) / 0.6), SEA + (height - SEA) * smooth((lake_e - 1) / 0.7))
# the river, from the lake's right-hand shore to the sea
RIVER = [(22, -8), (34, 12), (36, 34), (46, 56), (62, 78), (82, 108)]
dr = np.full(X.shape, 1e9)
for (ax, az), (bx, bz) in zip(RIVER, RIVER[1:]):
    t = np.clip(((X - ax) * (bx - ax) + (Z - az) * (bz - az)) / ((bx - ax) ** 2 + (bz - az) ** 2), 0, 1)
    dr = np.minimum(dr, np.hypot(X - (ax + t * (bx - ax)), Z - (az + t * (bz - az))))
dr = dr + 1.2 * (value_noise(8, 33) - 0.5)
height = np.where(dr < 2.7, 59.4, SEA + (height - SEA) * smooth((dr - 2.7) / 6.0))
height = np.where(d > 0, height, SEA + d * 170.0)
H = np.maximum(np.round(height).astype(int), FLOOR)
hmap = {(int(x), int(z)): int(H[i, j]) for i, x in enumerate(xs) for j, z in enumerate(xs)}
inland_water = {(x, z) for (x, z), h in hmap.items() if h < SEA and math.hypot(x, z) < coast[x + N, z + N] - 3}
# a strip of sand level with the water all round the lake and river, where reeds can stand
banks = set()
for (x, z) in inland_water:
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            p = (x + dx, z + dz)
            if hmap.get(p, 0) > SEA:
                banks.add(p)
for p in banks:
    hmap[p] = SEA
# the stream: a shallow channel straight down the mountain's near face into the lake
stream = [z for z in range(LAKE[1] - 14, MOUNT[1] + 4, -1) if hmap[(0, z)] >= SEA]
top = next((z for z in stream if hmap[(0, z)] >= 98), stream[-1])
stream = [z for z in stream if z >= top]
for z in stream:
    hmap[(0, z)] -= 1
SPRING = (0, hmap[(0, top)] + 1, top)
HMAX = max(hmap.values())


def top_material(h):
    return "sand" if h <= SEA + 2 else ("snow_block" if h >= 113 else ("stone" if h >= 99 else "dirt"))


def runs(cells, lo=-N, hi=N):
    """Merge a {(x, z): key} layer into rectangles: [(x1, z1, x2, z2, key)]."""
    rows = {}
    for z in range(lo, hi + 1):
        row, x = [], lo
        while x <= hi:
            m = cells.get((x, z))
            if m is None:
                x += 1
                continue
            x2 = x
            while x2 + 1 <= hi and cells.get((x2 + 1, z)) == m:
                x2 += 1
            row.append((x, x2, m))
            x = x2 + 1
        rows[z] = row
    out, open_ = [], {}
    for z in range(lo, hi + 2):
        cur = set(rows.get(z, []))
        for key in list(open_):
            if key not in cur:
                out.append((key[0], open_.pop(key), key[1], z - 1, key[2]))
        for key in cur:
            open_.setdefault(key, z)
    return out


layers = {}
for y in range(FLOOR + 1, HMAX + 1):
    cells = {}
    for (x, z), h in hmap.items():
        if h >= y:
            top = top_material(h)
            cells[(x, z)] = top if (y > h - 3 and top != "stone") else "stone"
    layers[y] = [fill(x1, z1, x2, z2, y, f"minecraft:{m}") for x1, z1, x2, z2, m in runs(cells)]


def zone(x, z, h=None):
    h = hmap.get((x, z), 0) if h is None else h
    if h >= 90 or math.hypot(x - MOUNT[0], z - MOUNT[1]) < 36:
        return "mountain"
    if x > 26 and z < -4:
        return "jungle"
    if x < -26 and z < -6:
        return "savanna"
    if x < -30:
        return "cherry"
    if x > 42:
        return "forest"
    return "meadow"


BIOME = {"mountain": "minecraft:meadow", "jungle": "minecraft:jungle", "savanna": "minecraft:savanna",
         "cherry": "minecraft:cherry_grove", "forest": "minecraft:flower_forest"}
coarse = {}
for cx in range(-N // 4, N // 4 + 1):
    for cz in range(-N // 4, N // 4 + 1):
        x, z = cx * 4 + 2, cz * 4 + 2
        if hmap.get((x, z), 0) > SEA - 4 and zone(x, z) in BIOME:
            coarse[(cx, cz)] = BIOME[zone(x, z)]
BIOMES = []
for x1, z1, x2, z2, b in runs(coarse, -N // 4, N // 4):
    wx1, wx2 = -(z2 * 4 + 3) - 1, -(z1 * 4) - 1
    BIOMES.append(f"fillbiome {wx1} 40 {x1 * 4} {wx2} 150 {x2 * 4 + 3} {b}")

grass_cols = [(x, z, h) for (x, z), h in hmap.items() if top_material(h) == "dirt" and h > SEA]
RING = 5.0
ring_of = lambda x, z: int(math.hypot(x, z - (S0 - 2)) / RING)   # green spreads away from the near shore
rings = {}
for x, z, h in grass_cols:
    rings.setdefault(ring_of(x, z), []).append((x, z, h))
NRINGS = max(rings) + 1

# trees stay out of the long view from the near shore over the clearing, the meadow and the lake
LAKE_S = LAKE[1] + 18                                             # the lake's near shore
open_view = lambda x, z: (abs(x) < 13 and z > MOUNT[1] + 30) or (abs(x) < 31 and LAKE_S - 6 < z < CLEAR_Z + 14)
near_people = lambda x, z, r=5: math.hypot(x, z - CLEAR_Z) < r
TREES = {  # zone: (chance, spacing, [(feature, weight)])
    "meadow": (0.12, 9, [("oak", 3), ("fancy_oak", 1), ("oak_bees_005", 1)]),
    "cherry": (1.0, 7, [("cherry", 7), ("birch", 2), ("oak_bees_005", 1)]),
    "forest": (1.0, 7, [("oak", 4), ("fancy_oak", 2), ("birch", 3)]),
    "jungle": (1.0, 6, [("jungle_tree_no_vine", 6), ("mega_jungle_tree", 1), ("jungle_bush", 3)]),
    "savanna": (1.0, 11, [("acacia", 1)]),
    "mountain": (1.0, 7, [("spruce", 3), ("pine", 2)]),
}
tree_sites, taken = [], []
cands = [c for c in grass_cols if 65 <= c[2] <= 98 and not open_view(c[0], c[1]) and not near_people(c[0], c[1], 13)]
random.shuffle(cands)
for x, z, h in cands:
    chance, space, kinds = TREES[zone(x, z, h)]
    if random.random() < chance and all((x - a) ** 2 + (z - b) ** 2 >= space * space for a, b in taken):
        taken.append((x, z))
        tree_sites.append((x, z, h, random.choices([k for k, _ in kinds], [w for _, w in kinds])[0]))
    if len(tree_sites) >= 300:
        break
tree_sites.sort(key=lambda t: -t[1])                         # nearest the viewer first
tree_grid = {}
for a, b in taken:
    tree_grid.setdefault((a // 8, b // 8), []).append((a, b))


def near_tree(x, z, r=3):
    return any((x - a) ** 2 + (z - b) ** 2 <= r * r
               for gx in (x // 8 - 1, x // 8, x // 8 + 1) for gz in (z // 8 - 1, z // 8, z // 8 + 1)
               for a, b in tree_grid.get((gx, gz), []))


open_cols = [c for c in grass_cols if not near_tree(c[0], c[1]) and not near_people(c[0], c[1], 4)]
FLOWERS = ["dandelion", "poppy", "cornflower", "oxeye_daisy", "azure_bluet", "allium", "wildflowers"]
GROUND = {  # zone: [(chance, what)]; what is a block, or "feature:<name>"
    "meadow": [(0.22, "short_grass"), (0.07, FLOWERS)],
    "cherry": [(0.14, "pink_petals"), (0.12, "short_grass"), (0.04, FLOWERS)],
    "forest": [(0.15, "short_grass"), (0.10, FLOWERS + ["lily_of_the_valley"]), (0.015, "sweet_berry_bush[age=3]"), (0.004, "pumpkin")],
    "jungle": [(0.24, "short_grass"), (0.12, "fern"), (0.035, "feature:bamboo_no_podzol"), (0.010, "melon")],
    "savanna": [(0.42, "short_grass")],
    "mountain": [(0.10, "short_grass"), (0.03, FLOWERS)],
}
plants, plant_cols = {}, set()


def plant(x, z, h, what):
    bx, bz = wb(x, z)
    cmd = (f"place feature minecraft:{what[8:]} {bx} {h + 1} {bz}" if what.startswith("feature:")
           else f"setblock {bx} {h + 1} {bz} minecraft:{what}")
    plants.setdefault(ring_of(x, z), []).append(cmd)
    plant_cols.add((x, z))


for x, z, h in open_cols:
    r, acc = random.random(), 0.0
    for chance, what in GROUND[zone(x, z, h)]:
        acc += chance
        if r < acc:
            if what in ("melon", "pumpkin") and open_view(x, z):
                break
            plant(x, z, h, random.choice(what) if isinstance(what, list) else what)
            break
for (x, z) in banks:                                          # reeds on the banks, lilies on the lake
    if random.random() < 0.16 and not open_view(x, z):
        bx, bz = wb(x, z)
        plants.setdefault(ring_of(x, z), []).append(f"fill {bx} {SEA + 1} {bz} {bx} {SEA + random.randint(2, 3)} {bz} minecraft:sugar_cane")
for (x, z) in inland_water:
    if lake_e[x + N, z + N] < 0.9 and random.random() < 0.018:
        bx, bz = wb(x, z)
        plants.setdefault(ring_of(x, z), []).append(f"setblock {bx} {SEA + 1} {bz} minecraft:lily_pad")
CAM0_S = (0.5, 66.0, S0 + 56.5)

# ---------------------------------------------------------------- creatures
# id -> (how it looks to someone who has no word for it, count, group)
CREATURES = {
    "cow": ("large and heavy, four legs, a patched hide, horns, a deep lowing voice", 9, "cattle"),
    "sheep": ("round and woolly, four thin legs, bleats, eats the grass", 12, "cattle"),
    "pig": ("pink, stout, a flat snout, grunts, roots in the ground", 7, "cattle"),
    "horse": ("tall and swift, long legs, a mane and a long tail", 8, "cattle"),
    "donkey": ("like the swift tall one but smaller, with long ears and a loud bray", 3, "cattle"),
    "rabbit": ("small, long ears, hops, very quick", 12, "creeping"),
    "frog": ("small, wet skin, leaps, croaks, a long tongue", 8, "creeping"),
    "turtle": ("carries a round shell on its back, slow on land, graceful in water", 6, "creeping"),
    "armadillo": ("small, covered in hard plates, rolls into a ball", 6, "creeping"),
    "bee": ("tiny, striped, hums, goes from flower to flower", 10, "creeping"),
    "llama": ("tall with a long woolly neck, proud, sometimes spits", 6, "beast"),
    "panda": ("big, round, black and white, sits and eats, rolls over", 5, "beast"),
    "camel": ("very tall, a hump on its back, long legs, kneels to rest", 4, "beast"),
    "chicken": ("a small bird that walks more than it flies, clucks, pecks at seeds", 8, "fowl"),
    "parrot": ("a bright bird of many colours that flies and copies sounds", 26, "fowl"),
    "cod": ("a plain brown fish that swims in shoals", 30, "sea"),
    "salmon": ("a long red-sided fish, strong, leaps", 18, "sea"),
    "tropical_fish": ("a small fish in bright colours and patterns", 36, "sea"),
    "squid": ("soft, dark, many arms, squirts black ink", 6, "sea"),
    "glow_squid": ("like the many-armed one, but it glows", 3, "sea"),
    "dolphin": ("sleek and grey, leaps out of the water, clicks and whistles, playful", 7, "sea"),
    "nautilus": ("a swimmer in a great coiled shell, with trailing arms", 4, "sea"),
}
KINDS = ["whale"] + list(CREATURES)          # the look query answers 1 + the index into this list
cherries = [t for t in tree_sites if t[3] == "cherry"]
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
json.dump({"kinds": KINDS,
           "look": {"whale": "enormous, the greatest of all that swim, shaped like the leaping grey one but vast",
                    **{k: v[0] for k, v in CREATURES.items()}},
           "selector": {"whale": "@e[tag=gen.whale]",
                        **{k: f"@e[type=minecraft:{k},tag=!gen.whale]" for k in CREATURES}},
           "places": PLACES},
          open(os.path.join(ROOT, "companion", "creatures.json"), "w"), indent=1)

free = [c for c in open_cols if (c[0], c[1]) not in plant_cols]
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


def summon(kind, x, y, z, extra=""):
    return f'summon minecraft:{kind} {pt(x, y, z)} {{PersistenceRequired:1b,Tags:["gen.made"]{extra}}}'


def appear(kind, x, y, z, extra=""):
    return [summon(kind, x, y, z, extra),
            f"particle minecraft:poof {pt(x, y + 0.6, z)} 0.4 0.5 0.4 0.02 14 force",
            f"particle minecraft:happy_villager {pt(x, y + 0.8, z)} 0.5 0.6 0.5 0 8 force"]


def from_earth(kind, pool):
    x, y, z = spot(pool)
    return appear(kind, x, y + (2 if kind == "bee" else 0), z) + [
        f'particle minecraft:block{{block_state:"minecraft:dirt"}} {pt(x, y + 0.2, z)} 0.4 0.3 0.4 0.1 24 force',
        f"particle minecraft:dust_plume {pt(x, y, z)} 0.3 0.2 0.3 0.02 10 force"]


# ---------------------------------------------------------------- the schedule
TIMING = {int(k): v for k, v in json.load(open(os.path.join(ROOT, "narration", "timing.json"))).items()}
T = lambda s: int(round(s * 20))
GAP = {2: 2.5, 3: 5.0, 5: 2.0, 7: 2.5, 9: 8.0, 10: 2.0, 11: 2.5, 12: 4.0, 13: 2.0, 16: 4.5, 19: 2.0,
       21: 3.0, 22: 2.5, 23: 2.0, 25: 3.0, 26: 2.0, 27: 6.0, 31: 2.5, 33: 2.5, 34: 4.0}
S, E, t = {}, {}, 6.0                       # six seconds of darkness before the first word
for v in range(1, 35):
    S[v] = T(t)
    E[v] = S[v] + T(TIMING[v]["duration"] * STRETCH)
    t = E[v] / 20 + GAP.get(v, 1.6)
END = T(t)


def tc(v, j, end=False):
    """Tick at which clause j of verse v starts (or ends)."""
    c = TIMING[v]["clauses"][j]
    return S[v] + T((c["end"] if end else c["start"]) * STRETCH)


def tw(v, phrase):
    """Tick at which a phrase of verse v is spoken (by its position within its clause)."""
    for c in TIMING[v]["clauses"]:
        i = c["text"].lower().find(phrase.lower())
        if i >= 0:
            return S[v] + T((c["start"] + i / len(c["text"]) * (c["end"] - c["start"])) * STRETCH)
    raise KeyError(f"verse {v} has no phrase {phrase!r}")


cues = {}


def at(tick, lines):
    cues.setdefault(int(tick), []).extend(lines if isinstance(lines, list) else [lines])


def sound(tick, name, vol=1.0, pitch=1.0, cat="ambient"):
    at(tick, f"execute as @a at @s run playsound {name} {cat} @s ~ ~ ~ {vol} {pitch} {min(vol, 1.0)}")


for v in range(1, 35):
    at(S[v] - T(PRE), f"execute as @a at @s run playsound {NS}:narration.god.v{v:02d} voice @s ~ ~ ~ 1 1 1")

DAY = f"time of {NS}:day"


def lapse(tick, end_tick, start, end, hold=None):
    """Run the day clock from start to end between two ticks, then hold it (at `hold` if the run wraps)."""
    n = max(1, int(end_tick) - int(tick))
    at(tick, [f"{DAY} set {start}", f"{DAY} rate {max(1.0, (end - start) / n):.2f}", f"{DAY} resume"])
    at(end_tick, [f"{DAY} pause", f"{DAY} set {end if hold is None else hold}"])


def bell(tick):
    sound(tick, "minecraft:block.bell.resonate", 0.9, 0.6)
    sound(tick, f"{NS}:sfx.bell", 0.8)


MUSIC = []          # (name, start tick): each piece runs until the next begins


def music(tick, name):
    MUSIC.append((name, int(tick)))
    at(tick, f"execute as @a at @s run playsound {NS}:music.{name} music @s ~ ~ ~ 0.55 1 0.55")


# ---- the first day
music(1, "deep")
sound(tc(2, 1), f"{NS}:sfx.deep", 0.9)
sound(tc(2, 1), "minecraft:ambient.underwater.loop", 0.5, 0.5)
SPIRIT0, SPIRIT1 = tc(2, 2), E[2] + 20
sound(SPIRIT0, f"{NS}:sfx.wind", 0.9)
sound(SPIRIT0, "minecraft:item.elytra.flying", 0.3, 0.5)
for k, tick in enumerate(range(SPIRIT0, SPIRIT1, 2)):      # a glimmer passes over the unseen water
    z = S0 + 60 - 110 * k / max(1, (SPIRIT1 - SPIRIT0) // 2)
    at(tick, [f"particle minecraft:glow {pt(0.5, 63.4, z)} 0.3 0.05 9 0 10 force",
              f"particle minecraft:end_rod {pt(0.5, 64.2, z)} 0.3 0.3 8 0.01 2 force"])
ORB = tw(3, "Let there be light") - 6
LIGHT = tc(3, 1)
orb_at = pt(0.5, 86, S0 - 16)
orb = lambda s: (f"transformation:{{translation:[{-s / 2:.3f}f,0f,{-0.7071 * s:.3f}f],left_rotation:[0.3827f,0f,0f,0.9239f],"
                 f"scale:[{s}f,{s}f,{s}f],right_rotation:[0f,0f,0f,1f]}}")
at(ORB, f'summon minecraft:block_display {orb_at} {{Tags:["gen.orb"],block_state:"minecraft:pearlescent_froglight",'
        f'brightness:{{sky:15,block:15}},view_range:40f,{orb(0.05)}}}')
at(ORB + 2, f"data merge entity @e[tag=gen.orb,limit=1] {{start_interpolation:0,interpolation_duration:{max(10, LIGHT - ORB - 4)},{orb(11)}}}")
for k, tick in enumerate(range(ORB, LIGHT, 2)):                # a gathering point of light, which needs no light to be seen
    r = 0.3 + 0.35 * k
    at(tick, f"particle minecraft:end_rod {orb_at} {r:.2f} {r:.2f} {r:.2f} 0.002 {30 + 14 * k} force")
sound(ORB, "minecraft:block.amethyst_block.resonate", 0.9, 0.5)
at(LIGHT, [f"particle minecraft:flash{{color:[1.0,1.0,0.9,1.0]}} {orb_at} 0 0 0 0 1 force",
           f"particle minecraft:end_rod {orb_at} 3 3 3 1.6 2200 force",
           f"particle minecraft:glow {orb_at} 8 8 8 0.5 500 force",
           f"particle minecraft:firework {orb_at} 2 2 2 0.9 400 force",
           f"data merge entity @e[tag=gen.orb,limit=1] {{start_interpolation:0,interpolation_duration:70,{orb(0.05)}}}"])
at(LIGHT + 75, "kill @e[tag=gen.orb]")
sound(LIGHT, f"{NS}:sfx.light", 1.0)
sound(LIGHT, "minecraft:block.beacon.activate", 0.9, 0.7)
sound(LIGHT + 12, "minecraft:block.amethyst_block.chime", 1.0, 0.8)
music(LIGHT + 10, "light")
lapse(tc(4, 1), E[4] + 10, 6000, 11800)                    # the light is divided from the darkness
lapse(tw(5, "and the darkness he called Night"), tc(5, 0, True) + 8, 11800, 18000)
at(tc(5, 1), "scoreboard players set #sunless gen 1")
lapse(tc(5, 1), E[5] + 20, 18000, 30000, 6000)             # evening and morning, wrapped while sunless
bell(E[5])
# ---- the second day: the mist, then the waters above
music(S[6], "firmament")
sound(S[6], "minecraft:ambient.underwater.enter", 0.7, 0.6)
LIFT = tw(7, "divided the waters")
sound(LIFT, f"{NS}:sfx.wind", 0.8, 1.2)
sound(LIFT, "minecraft:item.elytra.flying", 0.4, 0.8)
for tick in range(LIFT, E[7] + 30, 4):
    at(tick, "execute at @e[type=minecraft:marker,tag=gen.cam,limit=1] run particle minecraft:cloud ~ ~4 ~ 14 2 14 0.25 40 force")
lapse(tc(8, 1), E[8] + 24, 6000, 30000, 6000)
bell(E[8])
# ---- the third day: the dry land, and everything that grows
music(S[9], "earth")
STIR, RISE = tw(9, "be gathered together"), tw(9, "let the dry land appear")
for tick in range(STIR, RISE + 40, 5):
    at(tick, ["particle minecraft:bubble_pop 0 63 0 62 0.2 62 0.01 800 force",
              "particle minecraft:splash 0 63.2 0 60 0.3 60 0.2 700 force"])
sound(STIR, "minecraft:ambient.underwater.loop", 0.8, 0.8)
sound(RISE, f"{NS}:sfx.rise", 1.0)
sound(RISE, "minecraft:entity.warden.emerge", 0.9, 0.5)
sound(RISE + 70, "minecraft:entity.warden.dig", 0.9, 0.5)
under = [y for y in layers if y <= SEA]
above = [y for y in layers if y > SEA]
for k, y in enumerate(under):                               # the unseen part comes up quickly
    at(RISE + k * 2, layers[y])
RISE2 = RISE + len(under) * 2
step = max(2, (E[9] + T(GAP[9]) - 24 - RISE2) // len(above))
for k, y in enumerate(above):
    at(RISE2 + k * step, layers[y] + ["particle minecraft:splash 0 63.2 0 68 0.4 68 0.3 500 force",
                                      f"particle minecraft:cloud 0 {y} 0 45 0.5 45 0.02 80 force",
                                      f"particle minecraft:dust_plume 0 {y} 0 40 0.4 40 0.02 60 force"])
    if k % 5 == 0:
        sound(RISE2 + k * step, "minecraft:entity.generic.splash", 0.6, 0.5)
sound(tc(10, 1), "minecraft:ambient.underwater.exit", 0.7, 0.7)
_sx, _sz = wb(SPRING[0], SPRING[2])                         # the spring on the mountain starts to run
at(tc(10, 1), [f"setblock {_sx} {SPRING[1]} {_sz} minecraft:water", f"particle minecraft:splash {_sx} {SPRING[1] + 1} {_sz} 0.5 0.5 0.5 0.2 60 force"])
GREEN = tw(11, "grass")
gstep = max(1, (E[11] + T(GAP[11]) - GREEN) // (NRINGS + 2))
sound(GREEN, f"{NS}:sfx.growth", 0.9)
for k in range(NRINGS):
    cells = {(x, z): h for x, z, h in rings.get(k, [])}
    at(GREEN + k * gstep, [fill(x1, z1, x2, z2, h, "minecraft:grass_block replace minecraft:dirt")
                           for x1, z1, x2, z2, h in runs(cells)])
    at(GREEN + (k + 2) * gstep, plants.get(k, []))
    if k % 4 == 0:
        sound(GREEN + k * gstep, "minecraft:block.grass.place", 0.7, 0.7)


def grow(tick, site):
    x, z, h, kind = site
    bx, bz = wb(x, z)
    at(tick, [f"setblock {bx} {h + 1} {bz} minecraft:air", f"place feature minecraft:{kind} {bx} {h + 1} {bz}",
              f"particle minecraft:happy_villager {bx} {h + 4} {bz} 1.5 2.5 1.5 0 30 force",
              f"particle minecraft:composter {bx} {h + 2} {bz} 1 2 1 0 16 force"])


FIRST = 30
for k, site in enumerate(tree_sites[:FIRST]):               # "and the fruit tree yielding fruit"
    grow(max(tw(11, "the fruit tree"), GREEN + (ring_of(site[0], site[1]) + 3) * gstep) + k * 4, site)
T12a, T12b = tw(12, "and the tree yielding fruit"), E[12] + T(GAP[12]) - 20
for k, site in enumerate(tree_sites[FIRST:]):
    grow(T12a + k * (T12b - T12a) // len(tree_sites[FIRST:]), site)
    if k % 6 == 0:
        sound(T12a + k * (T12b - T12a) // len(tree_sites[FIRST:]), "minecraft:item.bone_meal.use", 0.8, 0.7)
sound(T12a, f"{NS}:sfx.growth", 0.9, 0.9)
lapse(S[13], E[13] + 30, 6000, 30000, 6000)
bell(E[13])
# ---- the fourth day. From here the day clock is one straight run (see the sky timeline).
music(S[14], "heavens")
lapse(S[14] + 10, E[14], 6000, 22300)                       # the sourceless light fails
at(S[15], "scoreboard players set #sunless gen 0")
lapse(S[15], E[15] + 20, 46300, 47700)                      # a glow gathers ahead
SUN, MOON, STARS = tw(16, "two great lights"), tw(16, "and the lesser light"), tc(16, 2)
lapse(SUN, MOON, 47700, 50400)                              # the greater light rises, straight ahead
lapse(MOON, STARS, 50400, 62800)                            # it sets; the lesser light rises
lapse(STARS, E[16] + 60, 62800, 67000)                      # he made the stars also
sound(SUN, f"{NS}:sfx.sun", 1.0)
sound(SUN, "minecraft:block.beacon.power_select", 0.9, 0.6)
sound(MOON + 20, "minecraft:block.amethyst_block.resonate", 0.9, 0.7)
sound(STARS, f"{NS}:sfx.stars", 1.0)
for k in range(10):
    sound(STARS + k * 7, "minecraft:block.amethyst_block.chime", 0.7, 0.9 + k * 0.1)
for tick in range(STARS + 10, E[16] + 70, 6):               # a few of them fall
    a = random.uniform(-70, 70)
    at(tick, f"particle minecraft:end_rod {pt(a * 1.5, random.uniform(150, 190), random.uniform(-80, 80))} 0.2 0.2 0.2 0.6 14 force")
lapse(S[17], E[17] + 10, 67000, 73000)                      # they take up their paths: dawn
lapse(tc(18, 0), tc(18, 0, True), 73000, 97000, 73000)      # one whole day and night
lapse(tc(18, 1), E[18], 73000, 78000)
lapse(S[19], E[19] + 30, 78000, 102000, 78000)
bell(E[19])
# ---- the fifth day: the waters and the air
music(S[20], "waters")
SEA_BOX = lambda: (random.uniform(-22, 22), random.uniform(57, 61), random.uniform(S0 + 10, S0 + 48))
SWIM = tw(20, "the moving creature") - 10
k = 0
for kind, (_, count, group) in CREATURES.items():
    if group == "sea" and kind != "dolphin":
        for i in range(count // 2):
            x, y, z = SEA_BOX()
            at(SWIM + (k % 30) * 3, [summon(kind, x, y, z), f"particle minecraft:bubble {pt(x, y, z)} 0.3 0.3 0.3 0.05 12 force",
                                     f"particle minecraft:splash {pt(x, 63.2, z)} 0.3 0.1 0.3 0.1 8 force"])
            k += 1
for i in range(4):                                          # the leaping ones leap
    x, z = random.uniform(-14, 14), random.uniform(S0 + 12, S0 + 22)
    at(SWIM + 14 + i * 9, [summon("dolphin", x, 61, z, ",Motion:[0.0d,0.75d,0.0d]"),
                           f"particle minecraft:splash {pt(x, 63.3, z)} 0.6 0.3 0.6 0.4 60 force"])
lake_water = [p for p in inland_water if lake_e[p[0] + N, p[1] + N] < 0.6]
for i in range(10):                                         # and the lake has its own
    x, z = random.choice(lake_water)
    at(SWIM + 20 + i * 5, [summon("salmon" if i % 2 else "cod", x + 0.5, 60.5, z + 0.5), f"particle minecraft:splash {pt(x + 0.5, 63.2, z + 0.5)} 0.3 0.1 0.3 0.1 10 force"])
sound(SWIM, "minecraft:entity.dolphin.splash", 0.8, 0.8)
sound(SWIM + 20, "minecraft:entity.dolphin.jump", 0.9, 1.0)
FOWL = tw(20, "and fowl that may fly")
air = lambda: (random.uniform(-26, 26), random.uniform(66, 78), random.uniform(S0 - 4, S0 + 20))
for i in range(12):
    x, y, z = air()
    at(FOWL + i * 4, appear("parrot", x, y, z, f",Variant:{i % 5}"))
sound(FOWL, f"{NS}:sfx.birds", 0.9)
sound(FOWL, "minecraft:entity.parrot.fly", 1.0, 1.0)
WHALES = tw(21, "great whales")
whale = lambda s: f',Invulnerable:1b,Tags:["gen.made","gen.whale"],attributes:[{{id:"minecraft:scale",base:{s}}}]'
at(WHALES, [summon("dolphin", -12, 54, S0 + 12, whale(9.0)).replace('Tags:["gen.made"],', ""),
            summon("dolphin", 15, 53, S0 + 8, whale(7.0)).replace('Tags:["gen.made"],', ""),
            f"particle minecraft:bubble {pt(0.5, 54, S0 + 12)} 10 3 4 0.1 200 force"])
sound(WHALES, f"{NS}:sfx.whale", 1.0)
sound(WHALES, "minecraft:entity.elder_guardian.ambient", 0.8, 0.5)
MOVETH = tw(21, "every living creature that moveth")
k = 0
for kind, (_, count, group) in CREATURES.items():
    if group == "sea" and kind != "dolphin":
        for i in range(count - count // 2):
            x, y, z = SEA_BOX()
            at(MOVETH + (k % 30) * 3, [summon(kind, x, y - 3, z), f"particle minecraft:bubble {pt(x, y - 3, z)} 0.3 0.3 0.3 0.05 12 force"])
            k += 1
for i in range(3):
    at(MOVETH + 20 + i * 12, summon("dolphin", random.uniform(-16, 16), 57, random.uniform(S0 + 14, S0 + 32)))
WINGED = tw(21, "and every winged fowl")
for i in range(8):
    x, z, h = edges[i % len(edges)]
    at(WINGED + 30 + i * 5, appear("chicken", x + 0.5, h + 1, z + 0.5))
for i in range(6):
    x, y, z = air()
    at(WINGED + 30 + i * 5, appear("parrot", x, y, z, f",Variant:{i % 5}"))
FILL, MULT = tw(22, "fill the waters"), tw(22, "and let fowl multiply")
for i in range(24):
    x, y, z = SEA_BOX()
    at(FILL + i * 2, summon(random.choice(["cod", "tropical_fish", "salmon"]), x, y, z))
for i in range(8):
    x, y, z = air()
    at(MULT + i * 4, appear("parrot", x, y + 4, z - 20, f",Variant:{i % 5}"))
sound(MULT, "minecraft:entity.parrot.ambient", 1.0, 1.0)
lapse(S[23], E[23] + 30, 78000, 102000, 78000)
bell(E[23])
# ---- the sixth day: the beasts of the earth
music(S[24], "beasts")
by_group = lambda g: [(k, c[1]) for k, c in CREATURES.items() if c[2] == g]
for v, order in ((24, [("cattle", "cattle"), ("creeping", "and creeping thing"), ("beast", "and beast of the earth")]),
                 (25, [("beast", "the beast of the earth"), ("cattle", "and cattle after their kind"), ("creeping", "and every thing that creepeth")])):
    for group, phrase in order:
        t0, i = tw(v, phrase), 0
        for kind, count in by_group(group):
            n = (count + 1) // 2 if v == 24 else count // 2
            for _ in range(n):
                at(t0 + i * 3, from_earth(kind, POOL.get(kind, meadow)))
                i += 1
sound(tw(24, "cattle"), "minecraft:entity.cow.ambient", 1.0, 0.9)
sound(tw(24, "cattle") + 25, "minecraft:entity.horse.ambient", 1.0, 1.0)
sound(tw(25, "and cattle after their kind"), "minecraft:entity.sheep.ambient", 1.0, 1.0)
# ---- man
music(S[26] - 20, "man")
at(S[26] - 20, "stopsound @a ambient")
BEAM = tw(26, "Let us make man")
man = ('{Tags:["gen.figure","gen.m_%s"],CustomName:"%s",Invulnerable:1b,PersistenceRequired:1b,Glowing:1b,'
       'Rotation:[%sf,0f],profile:{texture:"genesis:entity/%s"}}')
HIM, HER = tw(27, "created he him"), tw(27, "male and female") + 12
# Two shafts of light come down from the sky onto the places where they will stand, and dust rises in
# them. Each stops a little before its figure appears, so nothing is left hanging in the air (and in
# the player's eyes) when they wake there.
for (px, pz), stop in ((ADAM_S, HIM - 6), (EVE_S, HER - 6)):
    for k, tick in enumerate(range(BEAM, stop, 2)):
        foot = max(0.0, 46 - 2.3 * k)                           # the shaft's lower end, coming down
        at(tick, [f"particle minecraft:end_rod {pt(px, 70 + foot + 14, pz)} 0.12 8 0.12 0.002 22 force",
                  f"particle minecraft:glow {pt(px, 70 + foot + 14, pz)} 0.2 8 0.2 0 6 force"])
        if foot == 0:
            at(tick, [f"particle minecraft:dust_plume {pt(px, 69.1, pz)} 0.3 0.1 0.3 0.01 3 force",
                      f"particle minecraft:end_rod {pt(px, 70, pz)} 0.25 0.9 0.25 0.01 3 force"])
sound(BEAM, "minecraft:block.beacon.activate", 0.9, 0.5)
sound(BEAM, f"{NS}:sfx.heartbeat", 0.9)
for tick, who, name, p in ((HIM, "adam", "Adam", ADAM), (HER, "eve", "Eve", EVE)):
    at(tick, [f"summon minecraft:mannequin {p} " + man % (who, name, FACE, who),
              f"particle minecraft:flash{{color:[1.0,1.0,0.95,1.0]}} {p} 0 0 0 0 1 force",
              f"execute positioned {p} run particle minecraft:end_rod ~ ~1 ~ 0.3 0.8 0.3 0.25 120 force"])
    sound(tick, "minecraft:block.amethyst_block.resonate", 1.0, 0.8 if who == "adam" else 1.1)
AWAKE = E[27] + 34
at(AWAKE - 6, "effect give @a[tag=gen.viewer] minecraft:blindness 2 0 true")
at(AWAKE, f"function {NS}:awake")
sound(AWAKE, "minecraft:entity.player.breath", 1.0, 0.8)
sound(AWAKE + 10, "minecraft:block.beacon.activate", 0.7, 1.2)
for tick in range(tw(28, "And God blessed them"), E[28], 5):   # the blessing falls around them
    at(tick, f"particle minecraft:end_rod {pt(0.5, 77, CLEAR_Z - 10)} 7 1.5 7 0.004 4 force")   # ahead and overhead, not in their faces
for i in range(6):
    x, y, z = random.uniform(-20, 20), random.uniform(76, 84), CLEAR_Z - 30
    at(tw(28, "the fowl of the air") + i * 4, summon("parrot", x, y, z, f",Variant:{i % 5},Motion:[-0.5d,0.0d,0.0d]"))
at(tw(29, "every herb bearing seed"), ["give @a[tag=gen.human] minecraft:wheat_seeds 12"]
   + [f"particle minecraft:happy_villager {pt(0.5, 69.5, CLEAR_Z - 8)} 8 0.4 8 0 80 force"])
at(tw(29, "and every tree"), [f"particle minecraft:glow {pt(x + 0.5, h + 5, z + 0.5)} 2 2 2 0 40 force" for x, z, h, _ in tree_sites[:20]])
at(tw(29, "to you it shall be for meat"), ["give @a[tag=gen.human] minecraft:apple 6", "give @a[tag=gen.human] minecraft:sweet_berries 8",
                                           "give @a[tag=gen.human] minecraft:melon_slice 6"])
sound(tw(29, "to you it shall be for meat"), "minecraft:block.amethyst_block.chime", 1.0, 1.2)
at(tw(30, "every green herb"), f"particle minecraft:happy_villager {pt(0.5, 69.5, CLEAR_Z - 28)} 22 0.6 16 0 260 force")
lapse(tc(31, 0), tc(31, 0, True), 78000, 82500)             # very good: the long gold of afternoon
lapse(tc(31, 1), E[31] + 30, 82500, 90000)                  # evening; then night and all the host of stars
bell(E[31])
music(S[32], "rest")
lapse(tc(33, 0), tc(33, 0, True), 90000, 96300, 72300)      # the seventh morning: sunrise straight ahead
lapse(tc(33, 1), E[33] + 20, 72300, 73600)
lapse(S[34], E[34] + 40, 73600, 75200)
at(END, f"function {NS}:free")

# ---------------------------------------------------------------- the camera
cz = CLEAR_Z + 0.5
cam_keys = [(0, CAM0_S), (LIFT, CAM0_S), (E[7] + 30, (0.5, 74, S0 + 56.5)),
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
for (t0, p0), (t1, p1) in zip(cam_keys, cam_keys[1:]):
    assert t1 >= t0, (t0, t1)
    if p0 == p1:
        continue
    for tick in range(t0 + 1, t1 + 1):
        a = smooth((tick - t0) / (t1 - t0))
        x, y, z = (p0[i] + (p1[i] - p0[i]) * a for i in range(3))
        at(tick, f"tp @e[type=minecraft:marker,tag=gen.cam,limit=1] {-z:.3f} {y:.3f} {x:.3f}")
CAM0 = pt(*CAM0_S)

# ---------------------------------------------------------------- timeline function
for tick in sorted(cues):
    fn(f"cue/t{tick}", cues[tick])
    fn("timeline", f"execute if score #t gen matches {tick} run function {NS}:cue/t{tick}")

# ---------------------------------------------------------------- fixed functions
lx, ly, lz = LOBBY
text = lambda x, y, z, s, colour, scale: (
    f'summon minecraft:text_display {x} {y} {z} {{Tags:["gen.lobbytext"],billboard:"center",background:0,'
    f'brightness:{{sky:15,block:15}},text:{{text:"{s}",color:"{colour}"}},'
    f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[{scale}f,{scale}f,{scale}f],right_rotation:[0f,0f,0f,1f]}}}}')
fn("load", ["scoreboard objectives add gen dummy",
            f"execute unless score #phase gen matches 0.. run function {NS}:setup"])
fn("setup", ["scoreboard players set #phase gen 0", "scoreboard players set #t gen 0",
             "scoreboard players set #sunless gen 1", "scoreboard players set #count gen -1",
             "scoreboard players set #companion gen 0", "scoreboard players set #look gen 0",
             "scoreboard players set #cmode gen 0", "scoreboard players set #carrived gen 0",
             "difficulty peaceful"]
   + [f"gamerule minecraft:{g} {v}" for g, v in [
       ("spawn_mobs", "false"), ("spawn_monsters", "false"), ("spawn_phantoms", "false"),
       ("spawn_wandering_traders", "false"), ("spawn_patrols", "false"), ("advance_weather", "false"),
       ("keep_inventory", "true"), ("mob_griefing", "false"), ("send_command_feedback", "false"),
       ("log_admin_commands", "false"), ("show_advancement_messages", "false"), ("locator_bar", "false"),
       ("player_movement_check", "false"), ("max_command_sequence_length", "10000000"),
       ("max_block_modifications", "10000000"), ("spectators_generate_chunks", "true")]]
   + [f"time of {NS}:cut set 0", f"time of {NS}:cut pause", f"{DAY} set 6000", f"{DAY} pause",
      "forceload add -192 -136 -65 135", "forceload add -64 -136 39 135", "forceload add 40 -136 135 135", f"forceload add {lx - 8} {lz - 8} {lx + 10} {lz + 8}",
      f"setworldspawn {lx - 3} {ly} {lz}", f"schedule function {NS}:setup2 60t", f"schedule function {NS}:setup3 120t"])
fn("setup3", BIOMES)   # the different kinds of country, laid over the sea before any land exists
# The lobby is a short hall running east. The stones and their names are at the far end, so whoever
# walks up to choose is already facing the way everything will happen. That matters in VR, where the
# game cannot turn the player's head for them.
fn("setup2", [f"fill {lx - 7} {ly - 1} {lz - 7} {lx + 10} {ly + 5} {lz + 7} minecraft:barrier hollow",
              f"fill {lx - 6} {ly - 1} {lz - 6} {lx + 9} {ly - 1} {lz + 6} minecraft:black_concrete",
              f"setblock {lx + 3} {ly - 1} {lz - 3} minecraft:gold_block",
              f"setblock {lx + 3} {ly - 1} {lz + 3} minecraft:diamond_block",
              f"setblock {lx + 3} {ly + 2} {lz - 3} minecraft:light[level=15]",
              f"setblock {lx + 3} {ly + 2} {lz + 3} minecraft:light[level=15]",
              f"setblock {lx - 2} {ly + 2} {lz} minecraft:light[level=11]",
              "kill @e[tag=gen.lobbytext]", "kill @e[tag=gen.cam]",
              text(lx + 3.5, ly + 1.9, lz - 2.5, "ADAM", "gold", 1.6), text(lx + 3.5, ly + 1.9, lz + 3.5, "EVE", "aqua", 1.6),
              text(lx + 8.5, ly + 3.4, lz + 0.5, "GENESIS", "white", 3.2),
              text(lx + 8.5, ly + 2.3, lz + 0.5, "Stand on a stone to choose who you will be", "white", 1.1),
              f'summon minecraft:marker {CAM0} {{Tags:["gen.cam"]}}'])
fn("tick", [f"execute as @a[tag=!gen.seen] run function {NS}:join",
            f"execute if score #phase gen matches 0 run function {NS}:lobby",
            f"execute if score #phase gen matches 1 run function {NS}:intro",
            f"execute store result score #b gen run {DAY} query time",
            f"execute if score #sunless gen matches 1 if score #b gen matches 24000.. run {DAY} set 0",
            f"execute if score #b gen matches 96000.. run {DAY} set 72000",
            f"execute if score #phase gen matches 2 as @e[tag=gen.companion] at @s run function {NS}:companion/tick"])
fn("join", ["tag @s add gen.seen",
            f"execute if score #phase gen matches 0 run function {NS}:join_lobby",
            f"execute if score #phase gen matches 1 run function {NS}:join_viewer",
            f"execute if score #phase gen matches 2 run function {NS}:join_world"])
fn("join_lobby", ["tag @s add gen.lobby", "gamemode adventure @s", f"tp @s {lx - 2.5} {ly} {lz + 0.5} -90 0",
                  "effect give @s minecraft:saturation infinite 0 true", "effect give @s minecraft:resistance infinite 4 true",
                  'title @s times 20 80 20', 'title @s subtitle {text:"Walk to a stone to choose",color:"gray"}',
                  'title @s title {text:"Genesis"}'])
fn("join_viewer", ["tag @s add gen.viewer", "tag @s add gen.adam", "gamemode spectator @s"])
fn("join_world", ["tag @s add gen.human", "gamemode survival @s", f"tp @s {pt(0.5, 69, CLEAR_Z + 3.5)} {FACE} 0"])
fn("lobby", [f"execute as @a[tag=gen.lobby,tag=!gen.picked] at @s if block ~ ~-1 ~ minecraft:gold_block run function {NS}:pick_adam",
             f"execute as @a[tag=gen.lobby,tag=!gen.picked] at @s if block ~ ~-1 ~ minecraft:diamond_block run function {NS}:pick_eve",
             "execute if score #count gen matches -1 if entity @a[tag=gen.lobby] unless entity @a[tag=gen.lobby,tag=!gen.picked] run scoreboard players set #count gen 80",
             "execute if score #count gen matches 1.. run scoreboard players remove #count gen 1",
             f"execute if score #count gen matches 0 run function {NS}:start"])
for who, colour in (("adam", "gold"), ("eve", "aqua")):
    fn(f"pick_{who}", ["tag @s add gen.picked", f"tag @s add gen.{who}",
                       f'title @s subtitle {{text:"In the beginning...",color:"gray"}}',
                       f'title @s title {{text:"{who.capitalize()}",color:"{colour}"}}',
                       "playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 1 0.8"])
# no rotation is given here or on waking: the player keeps facing the way they were, which the lobby set
fn("start", ["scoreboard players set #phase gen 1", "scoreboard players set #t gen 0", "scoreboard players set #count gen -1",
             "scoreboard players set #sunless gen 1", f"{DAY} set 6000", f"{DAY} pause",
             f"time of {NS}:cut set 0", f"time of {NS}:cut rate 1", f"time of {NS}:cut resume",
             "tag @a[tag=gen.lobby] add gen.viewer", "tag @a remove gen.lobby", "gamemode spectator @a[tag=gen.viewer]",
             "title @a clear", "stopsound @a",
             f"tp @e[type=minecraft:marker,tag=gen.cam,limit=1] {CAM0}",
             f"tp @a[tag=gen.viewer] {CAM0}"])
fn("intro", ["scoreboard players add #t gen 1", f"function {NS}:timeline",
             "execute at @e[type=minecraft:marker,tag=gen.cam,limit=1] run tp @a[tag=gen.viewer] ~ ~ ~"])
fn("awake", ["tag @a[tag=gen.viewer] add gen.human", "tag @a remove gen.viewer", "gamemode survival @a[tag=gen.human]",
             "execute if entity @a[tag=gen.adam] run kill @e[tag=gen.m_adam]",
             "execute if entity @a[tag=gen.eve] run kill @e[tag=gen.m_eve]",
             "tag @e[tag=gen.figure] add gen.companion",
             "execute as @e[tag=gen.companion] run data merge entity @s {Glowing:0b}",
             "execute if entity @e[tag=gen.companion,tag=gen.m_eve] run scoreboard players set #companion gen 1",
             "execute if entity @e[tag=gen.companion,tag=gen.m_adam] run scoreboard players set #companion gen 2",
             f"tp @a[tag=gen.human,tag=gen.adam] {ADAM}",
             f"tp @a[tag=gen.human,tag=gen.eve] {EVE}",
             "effect clear @a[tag=gen.human] minecraft:resistance",
             "execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base set 0",
             "execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base set 0",
             "kill @e[type=minecraft:marker,tag=gen.target]",
             f'summon minecraft:marker {EVE} {{Tags:["gen.target"]}}'])
fn("free", ["scoreboard players set #phase gen 2", "scoreboard players set #cmode gen 1",
            "execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base reset",
            "execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base reset",
            f"{DAY} rate 1", f"{DAY} resume", "forceload remove all", "forceload add -48 -48 47 47",
            'title @a times 30 80 40', 'title @a subtitle {text:"The world is yours to name",color:"gray"}',
            'title @a title {text:"The seventh day",color:"white"}'])
# The companion. #cmode: 0 stay, 1 walk with the nearest person, 2 walk to the target marker.
WALK = "rotated ~ 0 positioned ^ ^ ^0.2 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~ ~ ~"
fn("companion/tick", [
    "execute unless entity @a[tag=gen.human,distance=..96] run return 0",
    "execute if score #cmode gen matches 1 unless entity @a[tag=gen.human,distance=..40] at @p[tag=gen.human] positioned ~1.5 ~ ~1.5 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~",
    f"execute if score #cmode gen matches 1 unless entity @a[tag=gen.human,distance=..3.6] facing entity @p[tag=gen.human] feet {WALK}",
    "execute if score #cmode gen matches 1 if entity @a[tag=gen.human,distance=..3.6] run rotate @s facing entity @p[tag=gen.human] eyes",
    f"execute if score #cmode gen matches 2 unless entity @e[type=minecraft:marker,tag=gen.target,distance=..1.7] facing entity @e[type=minecraft:marker,tag=gen.target,limit=1] feet {WALK}",
    f"execute if score #cmode gen matches 2 if entity @e[type=minecraft:marker,tag=gen.target,distance=..1.7] run function {NS}:companion/arrive",
    "execute if score #cmode gen matches 0 if entity @a[tag=gen.human,distance=..12] run rotate @s facing entity @p[tag=gen.human] eyes"])
fn("companion/arrive", ["scoreboard players set #cmode gen 0", "scoreboard players set #carrived gen 1"])
fn("companion/goto", ["$execute positioned $(x) 0 $(z) positioned over motion_blocking_no_leaves run tp @e[type=minecraft:marker,tag=gen.target,limit=1] ~ ~ ~",
                      "scoreboard players set #carrived gen 0", "scoreboard players set #cmode gen 2"])
fn("look/start", ["tag @e[tag=gen.looked] remove gen.looked", "scoreboard players set #ray gen 0",
                  "scoreboard players set #look gen 0", f"function {NS}:look/step"])
fn("look/step", [
    "execute positioned ~-0.5 ~-0.5 ~-0.5 as @e[type=#genesis:creature,dx=0,dy=0,dz=0,limit=1,sort=nearest] run tag @s add gen.looked",
    f"execute if entity @e[tag=gen.looked] run return run function {NS}:look/found",
    "execute unless block ~ ~ ~ #genesis:see_through run return 0",
    "scoreboard players add #ray gen 1",
    f"execute if score #ray gen matches ..70 positioned ^ ^ ^0.5 run function {NS}:look/step"])
fn("look/found", ["execute if entity @e[tag=gen.looked,tag=gen.whale] run scoreboard players set #look gen 1"]
   + [f"execute if entity @e[tag=gen.looked,type=minecraft:{k},tag=!gen.whale] run scoreboard players set #look gen {i + 1}"
      for i, k in enumerate(KINDS) if i > 0])

# ---------------------------------------------------------------- data files
shutil.rmtree(OUT, ignore_errors=True)
write("pack.mcmeta", {"pack": {"description": "Genesis: the creation of the world", "min_format": 121, "max_format": 121}})
for name, lines in funcs.items():
    write(f"data/{NS}/function/{name}.mcfunction", "\n".join(lines) + "\n")
write("data/minecraft/tags/function/load.json", {"values": [f"{NS}:load"]})
write("data/minecraft/tags/function/tick.json", {"values": [f"{NS}:tick"]})
write(f"data/{NS}/tags/entity_type/creature.json", {"values": [f"minecraft:{k}" for k in CREATURES]})
write(f"data/{NS}/tags/block/see_through.json", {"values": ["#minecraft:replaceable", "#minecraft:flowers", "minecraft:sweet_berry_bush", "minecraft:pink_petals", "minecraft:wildflowers"]})
write(f"data/{NS}/world_clock/day.json", {})
write(f"data/{NS}/world_clock/cut.json", {})
write(f"data/{NS}/worldgen/biome/eden.json", {
    "attributes": {"minecraft:gameplay/natural_mob_spawns": {"argument": {"spawn_costs": {}, "spawns_by_category": {
        c: [] for c in ["ambient", "axolotls", "creature", "misc", "monster", "underground_water_creature", "water_ambient", "water_creature"]}},
        "modifier": "overlay"}, "minecraft:visual/sky_color": "#78a7ff"},
    "carvers": [], "downfall": 0.4, "effects": {"water_color": "#3f76e4"}, "features": [],
    "has_precipitation": False, "temperature": 0.8})
dim = json.load(open(os.path.join(VANILLA, "dimension_type", "overworld.json")))
dim["default_clock"] = f"{NS}:day"
dim["timelines"] = [f"{NS}:sky", f"{NS}:cut"]
write("data/minecraft/dimension_type/overworld.json", dim)

# The sky. The day clock is scripted, not cyclic:
#   0..24000      light with no sun, moon or stars (days one to three), wrapped by the tick function
#   46300..72000  the fourth day: first sunrise, first sunset, first moonrise, the stars come out
#   72000..96000  the ordinary day, wrapped back to 72000 by the tick function
day = json.load(open(os.path.join(VANILLA, "timeline", "day.json")))
tracks = {}
for name, tr in day["tracks"].items():
    if name.split("/")[-1] in ("sun_angle", "moon_angle", "star_angle", "star_brightness"):
        continue
    kfs = [{"ticks": k["ticks"] + off, "value": k["value"]} for off in (0, 24000, 48000, 72000) for k in tr["keyframes"]]
    tracks[name] = {**tr, "keyframes": kfs}
kf = lambda pairs: {"keyframes": [{"ticks": int(a), "value": b} for a, b in pairs]}
tracks["minecraft:visual/sun_angle"] = kf([(0, 180.0), (46300, 180.0), (48000, 270.0), (54000, 360.0), (54000, 0.0), (60000, 90.0),
                                           (66000, 180.0), (72000, 270.0), (78000, 360.0), (78000, 0.0), (84000, 90.0), (90000, 180.0), (95999, 270.0)])
tracks["minecraft:visual/star_angle"] = tracks["minecraft:visual/sun_angle"]
tracks["minecraft:visual/moon_angle"] = kf([(0, 180.0), (58500, 180.0), (60000, 270.0), (66000, 360.0), (66000, 0.0), (72000, 90.0),
                                            (78000, 180.0), (84000, 270.0), (90000, 360.0), (90000, 0.0), (95999, 90.0)])
vs = day["tracks"]["minecraft:visual/star_brightness"]["keyframes"]
tracks["minecraft:visual/star_brightness"] = kf(
    [(0, 0.0), (63000, 0.0), (66400, 0.55)] + [(48000 + k["ticks"], k["value"]) for k in vs if k["ticks"] > 22000]
    + [(72000 + k["ticks"], k["value"]) for k in vs])
markers = {k: ({**v, "ticks": v["ticks"] + 72000} if isinstance(v, dict) else v + 72000) for k, v in day["time_markers"].items()}
write(f"data/{NS}/timeline/sky.json", {"clock": f"{NS}:day", "period_ticks": 96000, "time_markers": markers, "tracks": tracks})

# The intro's own layer on top of the sky: darkness, the first light, the mist, the clouds.
L0, L1 = LIGHT, LIGHT + 50
HEAVEN = tc(8, 0, True)
colour = lambda dark, warm, pale: {"keyframes": [
    {"ticks": 0, "value": dark}, {"ticks": L0, "value": dark}, {"ticks": L0 + 30, "value": warm}, {"ticks": L0 + 140, "value": pale},
    {"ticks": S[8], "value": pale}, {"ticks": HEAVEN, "value": "#ffffff"}], "modifier": "multiply"}
write(f"data/{NS}/timeline/cut.json", {"clock": f"{NS}:cut", "tracks": {
    "minecraft:visual/sky_color": colour("#000000", "#fff2d0", "#c4cad4"),
    "minecraft:visual/fog_color": colour("#000000", "#fff6e0", "#d2d6dc"),
    "minecraft:visual/sky_light_factor": {"keyframes": [{"ticks": 0, "value": 0.0}, {"ticks": L0, "value": 0.0}, {"ticks": L1, "value": 1.0}], "modifier": "multiply"},
    "minecraft:visual/cloud_color": {"keyframes": [{"ticks": 0, "value": "#00ffffff"}, {"ticks": LIFT, "value": "#00ffffff"},
                                                   {"ticks": E[7] + 40, "value": "#ffffffff"}], "modifier": "multiply"},
    "minecraft:visual/fog_start_distance": kf([(0, 0.0), (END, 0.0)]),
    "minecraft:visual/fog_end_distance": kf([(0, 26.0), (50, 1.5), (SPIRIT0 - 10, 1.5), (SPIRIT0 + 20, 70.0), (ORB, 70.0), (ORB + 12, 400.0),
                                             (L1 + 20, 1024.0), (S[6], 1024.0), (tc(6, 0, True), 10.0), (LIFT, 10.0),
                                             (E[7], 150.0), (E[7] + 30, 1024.0)]),
    "minecraft:audio/music_volume": kf([(0, 0.0), (END, 0.0), (END + 200, 1.0)])}})

MUSIC.sort(key=lambda m: m[1])
sections = [{"name": n, "start": s, "seconds": round(((MUSIC[i + 1][1] if i + 1 < len(MUSIC) else END + 300) - s) / 20, 1)}
            for i, (n, s) in enumerate(MUSIC)]
json.dump({"verse_start": S, "verse_end": E, "end": END, "kinds": KINDS, "music": sections,
           "marks": {"light": LIGHT, "rise": RISE, "green": GREEN, "sun": SUN, "moon": MOON, "stars": STARS,
                     "swim": SWIM, "whales": WHALES, "beam": BEAM, "him": HIM, "her": HER, "awake": AWAKE}},
          open(os.path.join(ROOT, "work", "schedule.json"), "w"))
ncmd = sum(len(v) for v in funcs.values())
print(f"intro {END / 20 / 60:.1f} min ({END} ticks), {len(cues)} cue ticks, {ncmd} commands, island top y={HMAX}, "
      f"{len(grass_cols)} grass columns, {len(tree_sites)} trees, meadow spots {len(meadow)}, edge spots {len(edges)}")
print("music:", [(s["name"], s["seconds"]) for s in sections])
