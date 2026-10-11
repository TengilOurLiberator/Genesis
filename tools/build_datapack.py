"""Generate the Genesis datapack: the island, the sky script and the timed intro.

    python tools\\build_datapack.py

Reads verse lengths from verses\\dry and the vanilla day timeline from work\\mcdata (made with the
server jar's data generator). Writes datapack\\genesis and companion\\creatures.json.
"""
import json, math, os, random, shutil, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "datapack", "genesis")
VANILLA = os.path.join(ROOT, "work", "mcdata", "vanilla", "data", "minecraft")
NS = "genesis"
random.seed(31)
rng = np.random.default_rng(31)

SEA = 62            # top water block
FLOOR = 42          # top of the sea bed
LOBBY = (1000, 100, 1000)

# Everything below is laid out on a "stage" with the viewer to the south looking north. The stage is
# then turned a quarter so that the viewer looks east: the first sunrise comes up straight ahead,
# behind the island, and the newly made man and woman face the sunset on the sixth day.
wp = lambda x, z: (-z, x)                      # stage point -> world point
wb = lambda x, z: (-z - 1, x)                  # stage block -> world block
yaw = lambda stage: (stage + 90 + 180) % 360 - 180


def fill(x1, z1, x2, z2, y, rest):
    return f"fill {-z2 - 1} {y} {x1} {-z1 - 1} {y} {x2} {rest}"


def pt(x, y, z):
    wx, wz = wp(x, z)
    return f"{wx:.2f} {y:.2f} {wz:.2f}"


CAM0_S = (0.5, 66.0, 120.5)
CAM0 = (wp(0.5, 120.5)[0], 66.0, wp(0.5, 120.5)[1])
ADAM = (wp(-1.5, 0.5)[0], 69.0, wp(-1.5, 0.5)[1])
EVE = (wp(2.5, 0.5)[0], 69.0, wp(2.5, 0.5)[1])

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
N = 90
xs = np.arange(-N, N + 1)
X, Z = np.meshgrid(xs, xs, indexing="ij")
R = np.hypot(X, Z)
TH = np.arctan2(Z, X)
coast = 68 + 7 * np.sin(3 * TH + 1.0) + 4 * np.sin(5 * TH + 2.2) + 2.5 * np.sin(9 * TH + 0.4)
d = 1 - R / coast                                   # 0 at the shore, 1 at the centre


def smooth(a):
    a = np.clip(a, 0, 1)
    return a * a * (3 - 2 * a)


def value_noise(scale, seed):
    g = np.random.default_rng(seed).random((2 * N // scale + 3, 2 * N // scale + 3))
    fx, fz = (X + N) / scale, (Z + N) / scale
    ix, iz = fx.astype(int), fz.astype(int)
    tx, tz = smooth(fx - ix), smooth(fz - iz)
    return (g[ix, iz] * (1 - tx) + g[ix + 1, iz] * tx) * (1 - tz) + (g[ix, iz + 1] * (1 - tx) + g[ix + 1, iz + 1] * tx) * tz


land = 1.2 + 2.2 * smooth(d / 0.12) + 4.0 * smooth((d - 0.1) / 0.7)
land += 24 * np.exp(-((X - 4) ** 2 + (Z + 38) ** 2) / (2 * 17 ** 2))      # the hill to the north
land += 9 * np.exp(-((X + 36) ** 2 + (Z - 8) ** 2) / (2 * 12 ** 2))       # a lower rise to the west
land += 7 * np.exp(-((X - 40) ** 2 + (Z - 2) ** 2) / (2 * 11 ** 2))       # and one to the east
land += (value_noise(12, 5) - 0.5) * 2.6 * smooth(d / 0.2)
height = np.where(d > 0, SEA + land, SEA + d * 70.0)
clearing = smooth((15 - np.hypot(X, Z)) / 6)                              # flat ground where they wake
height = height * (1 - clearing) + 68.0 * clearing
H = np.maximum(np.round(height).astype(int), FLOOR)
HMAX = int(H.max())


def top_material(h):
    return "sand" if h <= SEA + 2 else ("stone" if h >= 87 else "dirt")


def runs(mask_by_mat):
    """Merge a {(x, z): material} layer into rectangles: [(x1, z1, x2, z2, material)]."""
    rows = {}
    for z in range(-N, N + 1):
        row, x = [], -N
        while x <= N:
            m = mask_by_mat.get((x, z))
            if m is None:
                x += 1
                continue
            x2 = x
            while x2 + 1 <= N and mask_by_mat.get((x2 + 1, z)) == m:
                x2 += 1
            row.append((x, x2, m))
            x = x2 + 1
        rows[z] = row
    out, open_ = [], {}
    for z in range(-N, N + 2):
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
    for i, x in enumerate(xs):
        for j, z in enumerate(xs):
            h = H[i, j]
            if h >= y:
                top = top_material(h)
                cells[(int(x), int(z))] = top if y > h - 3 and top != "stone" else ("stone" if top != "sand" or y <= h - 3 else "sand")
    layers[y] = [fill(x1, z1, x2, z2, y, f"minecraft:{m}") for x1, z1, x2, z2, m in runs(cells)]

grass_cols = [(int(x), int(z), int(H[i, j])) for i, x in enumerate(xs) for j, z in enumerate(xs)
              if top_material(H[i, j]) == "dirt" and H[i, j] > SEA]
RING = 3.0
rings = {}
for x, z, h in grass_cols:
    rings.setdefault(int(math.hypot(x, z) / RING), []).append((x, z, h))
NRINGS = max(rings) + 1

# trees, bushes and flowers
corridor = lambda x, z: abs(x) < 7 and z > -4
tree_sites, taken = [], []
cands = [c for c in grass_cols if 66 <= c[2] <= 84 and math.hypot(c[0], c[1]) > 12 and not corridor(c[0], c[1])]
random.shuffle(cands)
for x, z, h in cands:
    if all((x - a) ** 2 + (z - b) ** 2 >= 49 for a, b in taken):
        taken.append((x, z))
        kind = random.choices(["oak", "fancy_oak", "birch", "cherry", "oak_bees_005"], [36, 14, 22, 20, 8])[0]
        tree_sites.append((x, z, h, kind))
    if len(tree_sites) >= 85:
        break
tree_sites.sort(key=lambda t: math.hypot(t[0], t[1]))
near_tree = lambda x, z, r=3: any((x - a) ** 2 + (z - b) ** 2 <= r * r for a, b in taken)
open_cols = [c for c in grass_cols if not near_tree(c[0], c[1]) and math.hypot(c[0], c[1]) > 4]
FLOWERS = ["dandelion", "poppy", "cornflower", "oxeye_daisy", "azure_bluet", "allium", "wildflowers", "pink_petals"]
plants, plant_cols = {}, set()
for x, z, h in open_cols:
    r = random.random()
    block = None
    if r < 0.20:
        block = "short_grass"
    elif r < 0.26:
        block = random.choice(FLOWERS)
    elif r < 0.275 and math.hypot(x, z) > 14:
        block = "sweet_berry_bush[age=3]"
    elif r < 0.279 and math.hypot(x, z) > 14:
        block = random.choice(["melon", "pumpkin"])
    if block:
        bx, bz = wb(x, z)
        plants.setdefault(int(math.hypot(x, z) / RING), []).append(f"setblock {bx} {h + 1} {bz} minecraft:{block}")
        plant_cols.add((x, z))

# ---------------------------------------------------------------- creatures
# id -> (how it looks to someone who has no word for it, count, where)
CREATURES = {
    "cow": ("large and heavy, four legs, a patched hide, horns, a deep lowing voice", 6, "land"),
    "sheep": ("round and woolly, four thin legs, bleats, eats the grass", 8, "land"),
    "pig": ("pink, stout, a flat snout, grunts, roots in the ground", 5, "land"),
    "horse": ("tall and swift, long legs, a mane and a long tail", 5, "land"),
    "donkey": ("like the swift tall one but smaller, with long ears and a loud bray", 3, "land"),
    "rabbit": ("small, long ears, hops, very quick", 8, "land"),
    "llama": ("tall with a long woolly neck, proud, sometimes spits", 4, "land"),
    "panda": ("big, round, black and white, sits and eats, rolls over", 3, "land"),
    "camel": ("very tall, a hump on its back, long legs, kneels to rest", 2, "land"),
    "armadillo": ("small, covered in hard plates, rolls into a ball", 4, "land"),
    "frog": ("small, wet skin, leaps, croaks, a long tongue", 5, "shore"),
    "turtle": ("carries a round shell on its back, slow on land, graceful in water", 4, "shore"),
    "chicken": ("a small bird that walks more than it flies, clucks, pecks at seeds", 8, "land"),
    "parrot": ("a bright bird of many colours that flies and copies sounds", 14, "air"),
    "bee": ("tiny, striped, hums, goes from flower to flower", 6, "air"),
    "cod": ("a plain brown fish that swims in shoals", 22, "sea"),
    "salmon": ("a long red-sided fish, strong, leaps", 12, "sea"),
    "tropical_fish": ("a small fish in bright colours and patterns", 26, "sea"),
    "squid": ("soft, dark, many arms, squirts black ink", 6, "sea"),
    "glow_squid": ("like the many-armed one, but it glows", 3, "sea"),
    "dolphin": ("sleek and grey, leaps out of the water, clicks and whistles, playful", 6, "sea"),
    "nautilus": ("a swimmer in a great coiled shell, with trailing arms", 4, "sea"),
}
KINDS = ["whale"] + list(CREATURES)          # index 1.. in the look query
json.dump({"kinds": KINDS,
           "look": {"whale": "enormous, the greatest of all that swim, shaped like the leaping grey one but vast",
                    **{k: v[0] for k, v in CREATURES.items()}},
           "selector": {"whale": "@e[tag=gen.whale]",
                        **{k: f"@e[type=minecraft:{k},tag=!gen.whale]" for k in CREATURES}}},
          open(os.path.join(ROOT, "companion", "creatures.json"), "w"), indent=1)

meadow = [c for c in open_cols if (c[0], c[1]) not in plant_cols and 65 <= c[2] <= 76 and c[1] > -18 and math.hypot(c[0], c[1]) > 6]
shore = [c for c in grass_cols if c[2] <= 66 and c[1] > 20] or meadow


def summon(kind, x, y, z, extra=""):
    return f'summon minecraft:{kind} {pt(x, y, z)} {{PersistenceRequired:1b,Tags:["gen.made"]{extra}}}'


def appear(kind, x, y, z, extra=""):
    return [summon(kind, x, y, z, extra),
            f"particle minecraft:poof {pt(x, y + 0.6, z)} 0.4 0.5 0.4 0.02 14 force",
            f"particle minecraft:happy_villager {pt(x, y + 0.8, z)} 0.5 0.6 0.5 0 8 force"]


# ---------------------------------------------------------------- the schedule
def clip_len(i):
    name = [f for f in sorted(os.listdir(os.path.join(ROOT, "verses", "dry"))) if f.startswith(f"{i:02d}_")][0]
    with wave.open(os.path.join(ROOT, "verses", "dry", name)) as w:
        return w.getnframes() / w.getframerate()


# seconds of world-making after each verse is spoken
GAPS = [4, 7, 9, 7, 10, 6, 10, 9, 17, 9, 11, 12, 9, 7, 7, 15, 6, 9, 9,
        11, 10, 8, 9, 10, 8, 6, 8, 6, 6, 5, 9, 6, 7, 6]
T = lambda s: int(round(s * 20))
S, E, t = {}, {}, 5.0                       # five seconds of darkness before the first word
for v in range(1, 35):
    S[v] = T(t)
    E[v] = T(t + clip_len(v))
    t += clip_len(v) + GAPS[v - 1]
END = T(t)
cues = {}


def at(tick, lines):
    cues.setdefault(int(tick), []).extend(lines if isinstance(lines, list) else [lines])


def sound(tick, name, vol=1.0, pitch=1.0, cat="ambient"):
    at(tick, f"execute as @a at @s run playsound {name} {cat} @s ~ ~ ~ {vol} {pitch} {min(vol, 1.0)}")


for v in range(1, 35):
    at(S[v], f"execute as @a at @s run playsound {NS}:narration.god.v{v:02d} voice @s ~ ~ ~ 1 1 1")

DAY = f"time of {NS}:day"


def lapse(tick, start, end, seconds, hold=None):
    """Run the day clock from start to end over the given seconds, then hold it (at `hold` if the run wraps)."""
    at(tick, [f"{DAY} set {start}", f"{DAY} rate {max(1.0, (end - start) / T(seconds)):.2f}", f"{DAY} resume"])
    at(tick + T(seconds), [f"{DAY} pause", f"{DAY} set {end if hold is None else hold}"])


bell = lambda tick: sound(tick, "minecraft:block.bell.resonate", 1.0, 0.6)

# ---- day one
sound(S[1] - 60, "minecraft:ambient.underwater.loop", 0.5, 0.5)
sound(S[2], "minecraft:ambient.underwater.loop", 0.7, 0.6)
sound(E[2] - 40, "minecraft:item.elytra.flying", 0.35, 0.5)
LIGHT = E[3] - 25
at(LIGHT, [f"particle minecraft:end_rod {pt(0.5, 76, 70)} 3 3 3 1.4 1800 force",
           f"particle minecraft:glow {pt(0.5, 76, 70)} 6 6 6 0.5 400 force",
           f"particle minecraft:flash{{color:[1.0,1.0,0.9,1.0]}} {pt(0.5, 76, 70)} 0 0 0 0 1 force"])
sound(LIGHT, "minecraft:block.beacon.activate", 1.0, 0.7)
sound(LIGHT + 10, "minecraft:block.amethyst_block.resonate", 1.0, 0.5)
sound(LIGHT + 30, "minecraft:block.amethyst_block.chime", 1.0, 0.8)
lapse(E[4], 6000, 12600, 6)                       # the light draws away: dusk
at(E[5], f"scoreboard players set #sunless gen 1")
lapse(E[5], 12600, 30000, 9, 6000)                      # evening and morning, wrapping at 24000 while sunless
bell(E[5] + T(9))
# ---- day two: mist, then the waters above
sound(S[6], "minecraft:ambient.underwater.enter", 0.8, 0.6)
sound(E[7], "minecraft:item.elytra.flying", 0.5, 0.8)
lapse(E[8], 6000, 30000, 8, 6000)
bell(E[8] + T(8))
# ---- day three: land
RISE = E[9]
sound(RISE, "minecraft:entity.warden.emerge", 1.0, 0.5)
sound(RISE + 60, "minecraft:entity.warden.dig", 1.0, 0.5)
sound(RISE + 140, "minecraft:entity.warden.emerge", 0.8, 0.6)
under = [y for y in layers if y <= SEA]
above = [y for y in layers if y > SEA]
for k, y in enumerate(under):                      # the unseen part comes up quickly
    at(RISE + k * 2, layers[y])
    if k % 3 == 0:
        at(RISE + k * 2, ["particle minecraft:bubble_pop 0 63 0 40 0.2 40 0.01 600 force",
                          "particle minecraft:splash 0 63.2 0 38 0.3 38 0.2 500 force"])
RISE2 = RISE + len(under) * 2
step = max(2, (T(GAPS[8]) - len(under) * 2 - 20) // len(above))
for k, y in enumerate(above):
    at(RISE2 + k * step, layers[y] + ["particle minecraft:splash 0 63.2 0 45 0.4 45 0.3 300 force",
                                      f"particle minecraft:cloud 0 {y} 0 30 0.5 30 0.02 60 force"])
    if k % 5 == 0:
        sound(RISE2 + k * step, "minecraft:entity.generic.splash", 0.6, 0.5)
sound(E[10], "minecraft:ambient.underwater.exit", 0.8, 0.7)
GREEN = E[11]
gstep = max(1, T(GAPS[10]) // (NRINGS + 2))
for k in range(NRINGS):
    cells = {(x, z): str(h) for x, z, h in rings.get(k, [])}
    at(GREEN + k * gstep, [fill(x1, z1, x2, z2, h, "minecraft:grass_block replace minecraft:dirt")
                           for x1, z1, x2, z2, h in runs(cells)])
    at(GREEN + (k + 2) * gstep, plants.get(k, []))
    if k % 4 == 0:
        sound(GREEN + k * gstep, "minecraft:block.grass.place", 0.8, 0.7)
TREES = E[12]
tstep = max(1, (T(GAPS[11]) - 20) // len(tree_sites))
for k, (x, z, h, kind) in enumerate(tree_sites):
    bx, bz = wb(x, z)
    at(TREES + k * tstep, [f"setblock {bx} {h + 1} {bz} minecraft:air", f"place feature minecraft:{kind} {bx} {h + 1} {bz}",
                           f"particle minecraft:happy_villager {bx} {h + 4} {bz} 1.5 2.5 1.5 0 30 force"])
    if k % 6 == 0:
        sound(TREES + k * tstep, "minecraft:item.bone_meal.use", 0.9, 0.7)
lapse(E[13], 6000, 30000, 8, 6000)
bell(E[13] + T(8))
# ---- day four: the sky is a straight run of the clock from here (see sky timeline)
lapse(E[14], 6000, 22300, 6)                       # the sourceless light fades
at(E[15], f"scoreboard players set #sunless gen 0")
lapse(E[15], 46300, 47500, 6)                      # a glow gathers in the east
lapse(E[16], 47500, 54000, 4)                      # the greater light rises to noon
lapse(E[16] + T(4), 54000, 60500, 3)               # and sets
lapse(E[16] + T(7), 60500, 64000, 3)               # the lesser light rises
lapse(E[16] + T(10), 64000, 67000, 5)              # the stars come out
sound(E[16], "minecraft:block.beacon.power_select", 1.0, 0.6)
sound(E[16] + T(7), "minecraft:block.amethyst_block.resonate", 1.0, 0.7)
for k in range(8):
    sound(E[16] + T(10) + k * 10, "minecraft:block.amethyst_block.chime", 0.8, 1.0 + k * 0.1)
lapse(E[17], 67000, 78000, 6)                      # they take up their paths; morning, then noon
lapse(E[18], 78000, 102000, 9, 78000)                     # one whole day and night (wraps at 96000)
lapse(E[19], 78000, 102000, 9, 78000)
bell(E[19] + T(9))
# ---- day five: the waters and the air
fish_tick = E[20]
sea_spots = [(random.uniform(-26, 26), random.uniform(52, 60), random.uniform(86, 114)) for _ in range(200)]
k = 0
for kind, (_, count, where) in CREATURES.items():
    if where == "sea" and kind not in ("dolphin",):
        for _ in range(count):
            x, y, z = sea_spots[k]
            at(fish_tick + (k % 40) * 4, [summon(kind, x, y, z), f"particle minecraft:bubble {pt(x, y, z)} 0.3 0.3 0.3 0.05 12 force"])
            k += 1
sound(fish_tick, "minecraft:entity.dolphin.splash", 0.8, 0.8)
at(E[21], [summon("dolphin", -16, 55, 96, ',Tags:["gen.made","gen.whale"],Invulnerable:1b,attributes:[{id:"minecraft:scale",base:9.0}]').replace('Tags:["gen.made"],', ""),
           summon("dolphin", 20, 54, 92, ',Tags:["gen.made","gen.whale"],Invulnerable:1b,attributes:[{id:"minecraft:scale",base:7.0}]').replace('Tags:["gen.made"],', "")])
sound(E[21], "minecraft:entity.elder_guardian.ambient", 1.0, 0.5)
sound(E[21] + 60, "minecraft:entity.dolphin.ambient_water", 1.0, 0.5)
for i in range(CREATURES["dolphin"][1]):
    at(E[21] + 20 + i * 12, summon("dolphin", random.uniform(-20, 20), 58, random.uniform(88, 110)))
air = [(random.uniform(-30, 30), random.uniform(68, 80), random.uniform(60, 96)) for _ in range(40)]
for i in range(CREATURES["parrot"][1]):
    x, y, z = air[i]
    at(E[21] + T(6) + i * 6, appear("parrot", x, y, z, f",Variant:{i % 5}"))
for i in range(CREATURES["parrot"][1], CREATURES["parrot"][1] + 10):   # be fruitful and multiply
    x, y, z = air[i]
    at(E[22] + i * 5, appear("parrot", x, y, z, f",Variant:{i % 5}"))
for i in range(30):
    x, y, z = sea_spots[100 + i]
    at(E[22] + i * 4, summon(random.choice(["cod", "tropical_fish", "salmon"]), x, y, z))
sound(E[22], "minecraft:entity.parrot.ambient", 1.0, 1.0)
lapse(E[23], 78000, 102000, 9, 78000)
bell(E[23] + T(9))
# ---- day six: the beasts of the earth
random.shuffle(meadow)
land_list = [(k, c[1]) for k, c in CREATURES.items() if c[2] in ("land", "shore") or k == "bee"]
i = 0
for kind, count in land_list:
    pool = shore if CREATURES[kind][2] == "shore" else meadow
    for n in range(count):
        x, z, h = pool[(i * 7) % len(pool)]
        tick = (E[24] if n < (count + 1) // 2 else E[25]) + (i % 50) * 3
        at(tick, appear(kind, x + 0.5, h + (3 if kind == "bee" else 1), z + 0.5)
           + [f"particle minecraft:block{{block_state:\"minecraft:dirt\"}} {pt(x + 0.5, h + 1.2, z + 0.5)} 0.4 0.3 0.4 0.1 20 force"])
        i += 1
sound(E[24], "minecraft:entity.cow.ambient", 1.0, 0.9)
sound(E[24] + 30, "minecraft:entity.horse.ambient", 1.0, 1.0)
sound(E[25], "minecraft:entity.sheep.ambient", 1.0, 1.0)
# ---- man
for k in range(S[26], E[27] - 40, 3):
    at(k, [f"particle minecraft:end_rod {ADAM[0]} {ADAM[1] + 1} {ADAM[2]} 0.25 0.7 0.25 0.01 5 force",
           f"particle minecraft:end_rod {EVE[0]} {EVE[1] + 1} {EVE[2]} 0.25 0.7 0.25 0.01 5 force"])
at(S[26], "stopsound @a ambient")
sound(S[27], "minecraft:block.amethyst_block.resonate", 0.8, 0.5)
at(E[27], "function genesis:awake")
sound(E[27], "minecraft:entity.player.breath", 1.0, 0.8)
sound(E[27] + 10, "minecraft:block.beacon.activate", 0.8, 1.2)
at(E[29], ["give @a[tag=gen.human] minecraft:apple 6", "give @a[tag=gen.human] minecraft:sweet_berries 8",
           "give @a[tag=gen.human] minecraft:melon_slice 6", "give @a[tag=gen.human] minecraft:wheat_seeds 12"]
   + [f"particle minecraft:glow {pt(x + 0.5, h + 5, z + 0.5)} 2 2 2 0 40 force" for x, z, h, _ in tree_sites[:14]])
sound(E[29], "minecraft:block.amethyst_block.chime", 1.0, 1.2)
lapse(E[31], 78000, 84300, 8)                      # a long golden evening
bell(E[31] + T(8))
lapse(E[32], 84300, 90000, 5)                      # night, the whole host of stars
lapse(E[33], 90000, 97000, 6, 73000)                      # the seventh morning
lapse(E[34], 73000, 74000, 5)
at(END, "function genesis:free")

# ---------------------------------------------------------------- the camera
cam_keys = [(0, CAM0_S), (E[7], CAM0_S), (E[7] + T(9), (0.5, 72, 120.5)),
            (E[10], (0.5, 72, 120.5)), (E[10] + T(8), (0.5, 86, 124.5)),
            (E[11], (0.5, 86, 124.5)), (E[11] + T(10), (0.5, 80, 98.5)),
            (E[12], (0.5, 80, 98.5)), (E[12] + T(11), (0.5, 84, 104.5)),
            (S[20], (0.5, 84, 104.5)), (E[20] - 20, (0.5, 64, 100.5)),
            (E[20] + 10, (0.5, 64, 100.5)), (E[20] + 70, (0.5, 55, 100.5)),
            (S[22], (0.5, 55, 100.5)), (S[22] + 80, (0.5, 66, 100.5)),
            (S[24], (0.5, 66, 100.5)), (E[24], (0.5, 76, 62.5)),
            (E[25], (0.5, 76, 62.5)), (E[25] + T(7), (0.5, 74, 44.5)),
            (S[26], (0.5, 74, 44.5)), (E[26], (0.5, 70.5, 16.5))]
for (t0, p0), (t1, p1) in zip(cam_keys, cam_keys[1:]):
    if p0 == p1:
        continue
    for tick in range(t0 + 1, t1 + 1):
        a = smooth((tick - t0) / (t1 - t0))
        x, y, z = (p0[i] + (p1[i] - p0[i]) * a for i in range(3))
        at(tick, f"tp @e[type=minecraft:marker,tag=gen.cam,limit=1] {-z:.3f} {y:.3f} {x:.3f}")

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
             "difficulty peaceful"]
   + [f"gamerule minecraft:{g} {v}" for g, v in [
       ("spawn_mobs", "false"), ("spawn_monsters", "false"), ("spawn_phantoms", "false"),
       ("spawn_wandering_traders", "false"), ("spawn_patrols", "false"), ("advance_weather", "false"),
       ("keep_inventory", "true"), ("mob_griefing", "false"), ("send_command_feedback", "false"),
       ("log_admin_commands", "false"), ("show_advancement_messages", "false"), ("locator_bar", "false"),
       ("player_movement_check", "false"), ("max_command_sequence_length", "10000000"),
       ("max_block_modifications", "10000000"), ("spectators_generate_chunks", "true")]]
   + [f"time of {NS}:cut set 0", f"time of {NS}:cut pause", f"{DAY} set 6000", f"{DAY} pause",
      "forceload add -144 -96 95 95", f"forceload add {lx - 8} {lz - 8} {lx + 8} {lz + 8}",
      f"setworldspawn {lx} {ly} {lz + 2}", f"schedule function {NS}:setup2 60t"])
fn("setup2", [f"fill {lx - 7} {ly - 1} {lz - 7} {lx + 7} {ly + 4} {lz + 7} minecraft:barrier hollow",
              f"fill {lx - 6} {ly - 1} {lz - 6} {lx + 6} {ly - 1} {lz + 6} minecraft:black_concrete",
              f"setblock {lx - 3} {ly - 1} {lz - 4} minecraft:gold_block",
              f"setblock {lx + 3} {ly - 1} {lz - 4} minecraft:diamond_block",
              f"setblock {lx - 3} {ly + 2} {lz - 4} minecraft:light[level=15]",
              f"setblock {lx + 3} {ly + 2} {lz - 4} minecraft:light[level=15]",
              f"setblock {lx} {ly + 2} {lz + 2} minecraft:light[level=12]",
              "kill @e[tag=gen.lobbytext]", "kill @e[tag=gen.cam]",
              text(lx - 2.5, ly + 1.9, lz - 3.5, "ADAM", "gold", 1.6), text(lx + 3.5, ly + 1.9, lz - 3.5, "EVE", "aqua", 1.6),
              text(lx + 0.5, ly + 3.2, lz - 5.5, "GENESIS", "white", 3.0),
              text(lx + 0.5, ly + 2.3, lz - 5.5, "Stand on a stone to choose who you will be", "white", 1.1),
              f'summon minecraft:marker {CAM0[0]} {CAM0[1]} {CAM0[2]} {{Tags:["gen.cam"]}}'])
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
fn("join_lobby", ["tag @s add gen.lobby", "gamemode adventure @s", f"tp @s {lx + 0.5} {ly} {lz + 3.5} 180 0",
                  "effect give @s minecraft:saturation infinite 0 true", "effect give @s minecraft:resistance infinite 4 true",
                  'title @s times 20 80 20', 'title @s subtitle {text:"Stand on a stone to choose",color:"gray"}',
                  'title @s title {text:"Genesis"}'])
fn("join_viewer", ["tag @s add gen.viewer", "tag @s add gen.adam", "gamemode spectator @s"])
fn("join_world", ["tag @s add gen.human", "gamemode survival @s", f"tp @s {pt(0.5, 69, 3.5)} {yaw(0)} 0"])
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
fn("start", ["scoreboard players set #phase gen 1", "scoreboard players set #t gen 0", "scoreboard players set #count gen -1",
             "scoreboard players set #sunless gen 1", f"{DAY} set 6000", f"{DAY} pause",
             f"time of {NS}:cut set 0", f"time of {NS}:cut rate 1", f"time of {NS}:cut resume",
             "tag @a[tag=gen.lobby] add gen.viewer", "tag @a remove gen.lobby", "gamemode spectator @a[tag=gen.viewer]",
             "title @a clear", "stopsound @a",
             f"tp @e[type=minecraft:marker,tag=gen.cam,limit=1] {CAM0[0]} {CAM0[1]} {CAM0[2]}",
             f"tp @a[tag=gen.viewer] {CAM0[0]} {CAM0[1]} {CAM0[2]} {yaw(180)} 0"])
fn("intro", ["scoreboard players add #t gen 1", f"function {NS}:timeline",
             "execute at @e[type=minecraft:marker,tag=gen.cam,limit=1] run tp @a[tag=gen.viewer] ~ ~ ~"])
man = "{Tags:[\"gen.companion\",\"gen.%s\"],CustomName:\"%s\",Invulnerable:1b,PersistenceRequired:1b,profile:{texture:\"genesis:entity/%s\"}}"
fn("awake", ["tag @a[tag=gen.viewer] add gen.human", "tag @a remove gen.viewer", "gamemode survival @a[tag=gen.human]",
             f"tp @a[tag=gen.human,tag=gen.adam] {ADAM[0]} {ADAM[1]} {ADAM[2]} {yaw(0)} 0",
             f"tp @a[tag=gen.human,tag=gen.eve] {EVE[0]} {EVE[1]} {EVE[2]} {yaw(0)} 0",
             "effect give @a[tag=gen.human] minecraft:blindness 2 0 true",
             "effect clear @a[tag=gen.human] minecraft:resistance",
             "execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base set 0",
             "execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base set 0",
             f"execute unless entity @a[tag=gen.eve] run summon minecraft:mannequin {EVE[0]} {EVE[1]} {EVE[2]} " + man % ("eve", "Eve", "eve"),
             "execute unless entity @a[tag=gen.eve] run scoreboard players set #companion gen 1",
             f"execute if entity @a[tag=gen.eve] unless entity @a[tag=gen.adam] run summon minecraft:mannequin {ADAM[0]} {ADAM[1]} {ADAM[2]} " + man % ("adam", "Adam", "adam"),
             "execute if entity @a[tag=gen.eve] unless entity @a[tag=gen.adam] run scoreboard players set #companion gen 2",
             "execute as @e[tag=gen.companion] at @s run rotate @s facing entity @p[tag=gen.human] eyes"])
fn("free", ["scoreboard players set #phase gen 2",
            "execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base reset",
            "execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base reset",
            f"{DAY} rate 1", f"{DAY} resume", "forceload remove all", "forceload add -32 -32 31 31",
            'title @a times 30 80 40', 'title @a subtitle {text:"The world is yours to name",color:"gray"}',
            'title @a title {text:"The seventh day",color:"white"}'])
fn("companion/tick", [
    "execute unless entity @a[tag=gen.human,distance=..64] run return 0",
    "execute unless entity @a[tag=gen.human,distance=..40] at @p[tag=gen.human] positioned ~1.5 ~ ~1.5 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~",
    "execute unless entity @a[tag=gen.human,distance=..4.5] facing entity @p[tag=gen.human] feet rotated ~ 0 positioned ^ ^ ^0.19 positioned over motion_blocking_no_leaves run tp @s ~ ~ ~",
    "rotate @s facing entity @p[tag=gen.human] eyes"])
fn("look/start", ["tag @e[tag=gen.looked] remove gen.looked", "scoreboard players set #ray gen 0",
                  "scoreboard players set #look gen 0", f"function {NS}:look/step"])
fn("look/step", [
    "execute positioned ~-0.5 ~-0.5 ~-0.5 as @e[type=#genesis:creature,dx=0,dy=0,dz=0,limit=1,sort=nearest] run tag @s add gen.looked",
    f"execute if entity @e[tag=gen.looked] run return run function {NS}:look/found",
    "execute unless block ~ ~ ~ #genesis:see_through run return 0",
    "scoreboard players add #ray gen 1",
    f"execute if score #ray gen matches ..70 positioned ^ ^ ^0.5 run function {NS}:look/step"])
# the look query answers with 1 + the index into KINDS, or 0 for nothing
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
    kf = [{"ticks": k["ticks"] + off, "value": k["value"]} for off in (0, 24000, 48000, 72000) for k in tr["keyframes"]]
    tracks[name] = {**tr, "keyframes": kf}
kf = lambda pairs: {"keyframes": [{"ticks": a, "value": b} for a, b in pairs]}
tracks["minecraft:visual/sun_angle"] = kf([(0, 180.0), (46300, 180.0), (48000, 270.0), (54000, 360.0), (54000, 0.0), (60000, 90.0),
                                           (66000, 180.0), (72000, 270.0), (78000, 360.0), (78000, 0.0), (84000, 90.0), (90000, 180.0), (95999, 270.0)])
tracks["minecraft:visual/star_angle"] = tracks["minecraft:visual/sun_angle"]
tracks["minecraft:visual/moon_angle"] = kf([(0, 180.0), (58500, 180.0), (60000, 270.0), (66000, 360.0), (66000, 0.0), (72000, 90.0),
                                            (78000, 180.0), (84000, 270.0), (90000, 360.0), (90000, 0.0), (95999, 90.0)])
vs = day["tracks"]["minecraft:visual/star_brightness"]["keyframes"]
tracks["minecraft:visual/star_brightness"] = kf(
    [(0, 0.0), (64300, 0.0), (66600, 0.5)] + [(48000 + k["ticks"], k["value"]) for k in vs if k["ticks"] > 22000]
    + [(72000 + k["ticks"], k["value"]) for k in vs])
markers = {k: ({**v, "ticks": v["ticks"] + 72000} if isinstance(v, dict) else v + 72000) for k, v in day["time_markers"].items()}
write(f"data/{NS}/timeline/sky.json", {"clock": f"{NS}:day", "period_ticks": 96000, "time_markers": markers, "tracks": tracks})

# The intro's own layer on top of the sky: darkness, the first light, the mist, the clouds.
L0, L1 = LIGHT, LIGHT + 90
mult = lambda dark, lit: {"keyframes": [{"ticks": 0, "value": dark}, {"ticks": L0, "value": dark}, {"ticks": L1, "value": lit}], "modifier": "multiply"}
write(f"data/{NS}/timeline/cut.json", {"clock": f"{NS}:cut", "tracks": {
    "minecraft:visual/sky_color": mult("#000000", "#ffffff"),
    "minecraft:visual/fog_color": mult("#000000", "#ffffff"),
    "minecraft:visual/sky_light_factor": mult(0.0, 1.0),
    "minecraft:visual/cloud_color": {"keyframes": [{"ticks": 0, "value": "#00ffffff"}, {"ticks": E[7], "value": "#00ffffff"},
                                                   {"ticks": E[7] + 200, "value": "#ffffffff"}], "modifier": "multiply"},
    "minecraft:visual/fog_start_distance": kf([(0, 0.0), (END, 0.0)]),
    "minecraft:visual/fog_end_distance": kf([(0, 26.0), (50, 1.5), (L0, 1.5), (L0 + 160, 320.0), (L0 + 220, 1024.0),
                                             (S[6], 1024.0), (S[6] + 110, 9.0), (E[7], 9.0), (E[7] + 150, 140.0), (E[7] + 210, 1024.0)]),
    "minecraft:audio/music_volume": kf([(0, 0.0), (END, 0.0), (END + 200, 1.0)])}})

json.dump({"verse_start": S, "verse_end": E, "end": END, "kinds": KINDS}, open(os.path.join(ROOT, "work", "schedule.json"), "w"))
ncmd = sum(len(v) for v in funcs.values())
print(f"intro {END / 20 / 60:.1f} min ({END} ticks), {len(cues)} cue ticks, {ncmd} commands, island top y={HMAX}, "
      f"{len(grass_cols)} grass columns, {len(tree_sites)} trees, land animals {sum(c for _, c in land_list)}")
