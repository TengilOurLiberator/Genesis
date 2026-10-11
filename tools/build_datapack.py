"""Generate the Genesis datapack: the island, the sky script and the timed intro.

    python tools\\build_datapack.py

Reads narration\\timing.json (when each clause of each verse is spoken) and the vanilla day timeline from
work\\mcdata (made with the server jar's data generator). Writes datapack\\genesis, companion\\creatures.json
and work\\schedule.json. Things happen on the words that call for them: see `tw()`.

Version 3: the island comes from tools\\terrain.py (a huge Eden with every kind of country), the country and
the creatures from tools\\biome_data.py, and God, in the sky, from tools\\god.py.
"""
import json, math, os, random, re, shutil, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import terrain, biome_data, god

OUT = os.path.join(ROOT, "datapack", "genesis")
VANILLA = os.path.join(ROOT, "work", "mcdata", "vanilla", "data", "minecraft")
NS = "genesis"
random.seed(31)
rng = np.random.default_rng(31)

SEA = 62            # top water block
FLOOR = 42          # top of the sea bed
LOBBY = (1000, 100, 1000)
_meta = json.load(open(os.path.join(ROOT, "narration", "meta.json")))   # written by make_godvoice.py
STRETCH = _meta["stretch"]  # how much the voice was slowed
PRE = _meta["pre"]          # seconds of swell at the start of every narration clip before the first word

# ---------------------------------------------------------------- the terrain
TER = terrain.build(31)
N = terrain.N                                   # 340: the stage runs from -N to N on both axes
assert N == 340 and terrain.SEA == SEA and terrain.FLOOR == FLOOR
H = TER["H"].astype(np.int32)                   # top solid block of each column, [x + N, z + N]
WAT = TER["water"].astype(np.int32)             # top water block of inland water above the sea, else -1
ZONE = TER["zone"].astype(np.int32)
ZN = TER["zones"]
ZI = terrain.ZI
S0, CLEAR_Z = TER["S0"], TER["CLEAR_Z"]         # the near shore, and the z of the clearing where they wake
LAKE, PEAK, SPRING = TER["lake"], TER["peak"], TER["spring"]
LAKE_S = LAKE["cz"] + LAKE["rz"]                # the lake's near shore
xs_ = np.arange(-N, N + 1)
X, Z = np.meshgrid(xs_, xs_, indexing="ij")
# The waking view must reach the lake: from the eyes of the man and the woman (1.62 above their feet on the clearing)
# the ground has to stay below the line of sight to the middle of the lake. The meadow of the terrain module lies
# 3 to 8 blocks higher than that, so it is lowered into a gentle slope down to the water, widest in the middle of
# the view and rising again into the hills on both sides.
_eye_z, _eye_y = CLEAR_Z + 1.5, 69 + 1.62
_aim = LAKE["cz"] + LAKE["rz"] - 4                     # the near edge of the water, so that all of the lake shows
_line = _eye_y - (_eye_y - (SEA + 1.0)) * (_eye_z - Z) / (_eye_z - _aim)
_ceil = np.floor(_line - 1.2) + 60.0 * terrain.smooth((np.abs(X) - 26.0) / 55.0) + 80.0 * terrain.smooth((Z - (CLEAR_Z - 9.0)) / 6.0)
_ceil = np.where(Z < LAKE["cz"] + LAKE["rz"] - 6, 999.0, _ceil)                 # the lake and everything beyond it is as it was
CARVED = int((H > _ceil).sum())
H = np.minimum(H, _ceil.astype(np.int32))
HMAX = int(H.max())

# Everything is laid out on a "stage" with the viewer to the south looking north. The stage is then
# turned a quarter so that the viewer looks east: the first sunrise comes up straight ahead, behind
# the hill, and it does so again on the seventh morning for the man and the woman.
wp = lambda x, z: (-z, x)                      # stage point -> world point
wb = lambda x, z: (-z - 1, x)                  # stage block -> world block
yaw = lambda stage: (stage + 90 + 180) % 360 - 180
FACE = yaw(180)                                # the direction everything happens in (east)


def fill(x1, z1, x2, z2, y, rest):
    return f"fill {-z2 - 1} {y} {x1} {-z1 - 1} {y} {x2} {rest}"


def box(x1, z1, x2, z2, y1, y2, block):
    """One block or a box of blocks, between stage corners (inclusive); a single cell becomes a setblock."""
    if x1 == x2 and z1 == z2 and y1 == y2:
        return f"setblock {-z1 - 1} {y1} {x1} {block}"
    return f"fill {-z2 - 1} {y1} {x1} {-z1 - 1} {y2} {x2} {block}"


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


# ---------------------------------------------------------------- the island, as layers of blocks
BZ = biome_data.BIOMES
assert all(z in BZ for z in ZN), [z for z in ZN if z not in BZ]
BLOCK_NAMES = ["none"]


def bid(name):
    if name not in BLOCK_NAMES:
        BLOCK_NAMES.append(name)
    return BLOCK_NAMES.index(name)


STONE = bid("stone")
BAREA = np.array([bid(BZ[z]["bare"]) for z in ZN])
UNDERA = np.array([bid(BZ[z]["under"]) for z in ZN])
GREENA = np.array([bid(BZ[z]["green"]) if BZ[z]["green"] else 0 for z in ZN])
BANDA = np.array(["terraces" in BZ[z] for z in ZN])
BARE, UNDER, GREENK, BANDM = BAREA[ZONE], UNDERA[ZONE], GREENA[ZONE], BANDA[ZONE]
_br, _y, BAND_ID = random.Random(5), 0, {}
while _y < 280:                                                  # horizontal colour bands for the badlands
    _n, _c = _br.choice([1, 1, 2, 2, 3]), _br.choice(biome_data.BADLANDS_BANDS)
    for _k in range(_n):
        BAND_ID[_y + _k] = bid(_c)
    _y += _n

depth = np.where(WAT > H, WAT - H, np.where(H < SEA, SEA - H, 0))     # water above the bed
wet = depth > 0
dry = ~wet & (H >= SEA)


def rects(K):
    """Merge a keyed layer K[x + N, z + N] (0 = nothing) into boxes: [(x1, z1, x2, z2, key)] in stage coordinates."""
    Kt = np.ascontiguousarray(K.T)
    nz, nx = Kt.shape
    out, open_ = [], {}
    for z in range(nz + 1):
        cur = set()
        if z < nz:
            row = Kt[z]
            d = np.flatnonzero(row[1:] != row[:-1]) + 1
            for a, b in zip([0] + d.tolist(), d.tolist() + [nx]):
                k = int(row[a])
                if k:
                    cur.add((a, b - 1, k))
        for key in list(open_):
            if key not in cur:
                out.append((key[0] - N, open_.pop(key) - N, key[1] - N, z - 1 - N, key[2]))
        for key in cur:
            open_.setdefault(key, z)
    return out


def key_layer(y):
    """What stands in each column at height y: stone, three of the under block, the bare block on top."""
    d = H - y
    band = BAND_ID[y]
    stone_k = np.where(BANDM, band, STONE)
    under_k = np.where(BANDM, band, UNDER)
    return np.where(d >= 4, stone_k, np.where(d >= 1, under_k, np.where(d == 0, BARE, 0))).astype(np.int16)


# the hidden base: everything up to y = 50 is laid before anyone sees anything (the sea is dark and deep here)
BASE_TOP = 50
open_b, base_cmds = {}, []
for y in range(FLOOR, BASE_TOP + 2):
    cur = set()
    if y <= BASE_TOP:
        K = key_layer(y)
        if y == FLOOR:                                          # the flat world already has sand on the floor
            K = np.where((H == FLOOR) & (BARE == bid("sand")), 0, K).astype(np.int16)
        if y == BASE_TOP:                                       # the top of the hidden base is sand, like the sea floor, so it does not show
            K = np.where((H > BASE_TOP) & (K != 0), bid("sand"), K).astype(np.int16)
        cur = set(rects(K))
    for r in list(open_b):
        if r not in cur:
            y0 = open_b.pop(r)
            base_cmds.append(box(r[0], r[1], r[2], r[3], y0, y - 1, BLOCK_NAMES[r[4]]))
    for r in cur:
        open_b.setdefault(r, y)

# the biomes, on a 4 x 4 grid laid over the whole stage, ocean zones included
G4 = (2 * N + 4) // 4
cell = np.zeros((G4, G4), dtype=np.int16)
for gx in range(G4):
    for gz in range(G4):
        cell[gx, gz] = ZONE[min(2 * N, gx * 4 + 2), min(2 * N, gz * 4 + 2)] + 1
biome_cmds = []
_Kc =np.zeros((2 * N + 1, 2 * N + 1), dtype=np.int16)
_Kc[:G4, :G4] = cell
for x1, z1, x2, z2, k in rects(_Kc):                            # coordinates here are (index - N); undo that
    gx1, gz1, gx2, gz2 = x1 + N, z1 + N, x2 + N, z2 + N
    xa, xb = -N + gx1 * 4, -N + gx2 * 4 + 3                    # stage x range
    za, zb = -N + gz1 * 4, -N + gz2 * 4 + 3                    # stage z range
    nm = ZN[k - 1]
    area = (xb - xa + 1) * (zb - za + 1)
    parts = max(1, math.ceil(area * 164 / 8_000_000))           # stay well below the block modification limit
    for p in range(parts):
        zp1 = za + (zb - za + 1) * p // parts
        zp2 = za + (zb - za + 1) * (p + 1) // parts - 1
        biome_cmds.append(f"fillbiome {-zp2 - 1} 40 {xa} {-zp1 - 1} 203 {xb} minecraft:{nm}")

# ---- the rise of the land (day three), layer by layer from y = 51 up
RISE_LAYERS = {}
for y in range(BASE_TOP + 1, HMAX + 1):
    RISE_LAYERS[y] = [box(x1, z1, x2, z2, y, y, BLOCK_NAMES[k]) for x1, z1, x2, z2, k in rects(key_layer(y))]

# ---- water that stands above the sea: lakes and rivers, filled after the rise
WATER_LAYERS = {}
for y in range(SEA + 1, int(WAT.max()) + 1):
    m = ((WAT >= y) & (H < y)).astype(np.int16)
    if m.any():
        WATER_LAYERS[y] = [box(x1, z1, x2, z2, y, y, "water") for x1, z1, x2, z2, _ in rects(m)]

# ---- rules of the stage: nothing tall in the long view from the near shore to the lake, in the meadow
# between the lake and the clearing, or round the clearing
OPEN_VIEW = ((np.abs(X) < 13) & (Z >= LAKE["cz"])) | ((np.abs(X) < 34) & (Z > LAKE_S - 6) & (Z < CLEAR_Z + 14))
NEAR_CLEAR = np.hypot(X, Z - CLEAR_Z) < 13
NO_TALL = OPEN_VIEW | NEAR_CLEAR
NEAR_PEOPLE = np.hypot(X, Z - CLEAR_Z) < 4
_st = TER["stream"]
STREAM = np.zeros(H.shape, bool)
for _x, _z in _st:
    STREAM[N - 2:N + 3, _z + N] = True
slope = np.zeros(H.shape, np.int32)
for _dx, _dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    slope = np.maximum(slope, np.abs(H - np.roll(np.roll(H, _dx, 0), _dz, 1)))


def dilate(m, r):
    out = m.copy()
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            if dx * dx + dz * dz <= r * r:
                out |= np.roll(np.roll(m, dx, 0), dz, 1)
    return out


# ---- trees, by country, with spacing
def no_bees(feature):
    """Trees with a bee nest would let loose bees that are not ours (no tag, not persistent): use the plain tree."""
    base = re.sub(r"_bees(_\d+)?$", "", feature)
    return "birch_tall" if base == "super_birch" else base


TREE_CFG = {ZI[z]: (b["trees"], b["tree_spacing"], b["tree_chance"]) for z, b in BZ.items() if b["trees"]}
hi5 = H.copy()                                                  # a tree needs room round its trunk: no wall of ground beside it
for _dx in range(-2, 3):
    for _dz in range(-2, 3):
        hi5 = np.maximum(hi5, np.roll(np.roll(H, _dx, 0), _dz, 1))
tree_ok = dry & (H >= SEA + 1) & (H <= 175) & (hi5 - H <= 1) & ~NO_TALL & ~STREAM & np.isin(ZONE, list(TREE_CFG))
cand = np.argwhere(tree_ok)
rng.shuffle(cand)
tree_sites, tgrid = [], {}
for i, j in cand:
    zi = int(ZONE[i, j])
    kinds_, sp, chance = TREE_CFG[zi]
    sp = sp * 0.6                         # biome_data's spacing is for a sparse look; this packs the woods like vanilla
    if rng.random() >= chance:
        continue
    gx, gz = int(i) // 16, int(j) // 16
    if any((i - a) ** 2 + (j - b) ** 2 < max(sp, s2) ** 2
           for dx in (-1, 0, 1) for dz in (-1, 0, 1) for a, b, s2 in tgrid.get((gx + dx, gz + dz), ())):
        continue
    tgrid.setdefault((gx, gz), []).append((int(i), int(j), sp))
    feats, wts = zip(*kinds_)
    tree_sites.append((int(i) - N, int(j) - N, int(H[i, j]), no_bees(random.choices(feats, wts)[0]), ZN[zi]))
TREE_AT = np.zeros(H.shape, bool)
for x, z, h, kind_, zn_ in tree_sites:
    TREE_AT[x + N, z + N] = True
NEAR_TREE = dilate(TREE_AT, 3)

# ---- ground cover and the larger extras
SHORT_FEATURES = {"wildflower", "leaf_litter", "dry_grass", "taiga_grass"}
OCEANS = {"warm_ocean", "lukewarm_ocean", "ocean", "cold_ocean", "frozen_ocean"}
WATERZ = OCEANS | {"river", "frozen_river"}
SEA_DENSITY = np.clip(1.0 - (np.hypot(X, Z - (S0 + 35)) - 100) / 160.0 * 0.8, 0.2, 1.0)      # sea bed: full near the stage
SEA_DENSITY = np.where(np.hypot(X, Z - (S0 + 35)) > 330, 0.07, SEA_DENSITY)
R1, R2 = rng.random(H.shape), rng.random(H.shape)
ground = {}                      # (x, z) -> ("block" | "feature", name)
for zi, zn_ in enumerate(ZN):
    B = BZ[zn_]
    if not B["ground"] and not B["extras"]:
        continue
    if zn_ in WATERZ:
        ok = wet & (depth >= 2) & (ZONE == zi)
    else:
        ok = dry & (ZONE == zi) & ~NEAR_TREE & ~NEAR_PEOPLE & ~STREAM
    for i, j in np.argwhere(ok):
        x, z = int(i) - N, int(j) - N
        dens = float(SEA_DENSITY[i, j]) if zn_ in WATERZ else 1.0
        pick, acc = None, 0.0
        for chance, what in B["extras"]:                         # the big things, only where there is room
            if R2[i, j] < chance * dens and not NO_TALL[i, j]:
                pick = what
                break
        if pick is None:
            r = R1[i, j] / dens if dens > 0 else 9.0
            for chance, what in B["ground"]:
                acc += chance
                if r < acc:
                    pick = what
                    break
        if pick is None:
            continue
        if isinstance(pick, list):
            pick = random.choice(pick)
        if NO_TALL[i, j]:
            if pick.startswith("feature:"):
                if pick[8:] not in SHORT_FEATURES:
                    continue
            elif pick in ("pumpkin", "melon"):
                continue
        ground[(x, z)] = ("feature", pick[8:]) if pick.startswith("feature:") else ("block", pick)
DECO = np.zeros(H.shape, bool)
for (x, z) in ground:
    DECO[x + N, z + N] = True
    if NO_TALL[x + N, z + N]:                                    # the stage rules, checked
        what_, name_ = ground[(x, z)]
        assert (name_ in SHORT_FEATURES) if what_ == "feature" else name_ not in ("pumpkin", "melon"), (x, z, name_)
assert not any(NO_TALL[x + N, z + N] for x, z, *_ in tree_sites), "a tree stands in the long view or near the clearing"

# ---- deep snow, laid where nothing else will stand
SNOWZ = np.array([BZ[z]["deep_snow"] for z in ZN])[ZONE]
snow_ok = SNOWZ & dry & ~DECO & ~TREE_AT & ~STREAM & ~NEAR_PEOPLE
_sn = terrain.fnoise(np.random.default_rng(3), 40.0, 8.0)
SNOW_LAYERS = np.where(snow_ok, 1 + (_sn > -0.3).astype(int) + (_sn > 0.5).astype(int) + (_sn > 1.2).astype(int), 0).astype(np.int16)
SNOW_COLS = int(snow_ok.sum())
SNOW_LAYER_CMDS = {}
for y in range(SEA + 2, HMAX + 2):
    m = np.where(H + 1 == y, SNOW_LAYERS, 0).astype(np.int16)
    if m.any():
        SNOW_LAYER_CMDS[y] = [box(x1, z1, x2, z2, y, y, f"snow[layers={k}]") for x1, z1, x2, z2, k in rects(m)]

# ---- the green that spreads out from the near shore, ring by ring
RING = 8.0
RINGS = (np.hypot(X, Z - (S0 - 2)) / RING).astype(np.int32)
green_ok = dry & (GREENK > 0) & (H >= SEA)
NRINGS = int(RINGS[green_ok].max()) + 1
WAVE = {}                         # ring -> fill commands that turn bare earth into grass (or podzol, or mycelium)
for y in range(SEA, HMAX + 1):
    m = np.where(green_ok & (H == y), RINGS * 64 + GREENK, 0).astype(np.int32)
    if m.any():
        for x1, z1, x2, z2, k in rects(m):
            WAVE.setdefault(k // 64, []).append(box(x1, z1, x2, z2, y, y, BLOCK_NAMES[k % 64]))
assert len(BLOCK_NAMES) < 64
plants = {}                       # ring -> commands
for (x, z), (what, name) in ground.items():
    h = int(H[x + N, z + N])
    bx, bz = wb(x, z)
    if what == "feature":
        cmd = (f"place feature {name} {bx} {h + 1} {bz}", 25.0)
    else:
        cmd = (f"setblock {bx} {h + 1} {bz} {name}", 3.0)
    plants.setdefault(int(RINGS[x + N, z + N]), []).append(cmd)
tree_sites.sort(key=lambda t: (int(RINGS[t[0] + N, t[1] + N]), t[1]))
caves = TER["caves"]
CAVE_CMDS = [box(x1, z1, x2, z2, y1, y2, "air") for x1, y1, z1, x2, y2, z2 in caves]
CAM0_S = (0.5, 66.0, S0 + 56.5)

# ---------------------------------------------------------------- creatures
EXCLUDED_ANIMALS = {"allay", "happy_ghast", "sniffer", "mooshroom"}      # only animals that exist in the real world
ANIM = {k: v for k, v in biome_data.ANIMALS.items() if k not in EXCLUDED_ANIMALS}
KINDS = ["whale"] + list(ANIM)          # the look query answers 1 + the index into this list
WHALE_LOOK = "enormous, the greatest of all that swim, shaped like the leaping grey one but vast"
zone_idx = lambda names: [ZI[n] for n in names if n in ZI]


def summon(kind, x, y, z, extra="", tags=("gen.made",)):
    tg = ",".join(f'"{t}"' for t in tags)
    return f'summon minecraft:{kind} {pt(x, y, z)} {{Invulnerable:1b,PersistenceRequired:1b,Tags:[{tg}]{"," + extra if extra else ""}}}'


def appear(kind, x, y, z, extra=""):
    return [summon(kind, x, y, z, extra),
            f"particle minecraft:poof {pt(x, y + 0.6, z)} 0.4 0.5 0.4 0.02 14 force",
            f"particle minecraft:happy_villager {pt(x, y + 0.8, z)} 0.5 0.6 0.5 0 8 force"]


def from_earth(kind, x, y, z, extra=""):
    return appear(kind, x, y, z, extra) + [
        f'particle minecraft:block{{block_state:"minecraft:dirt"}} {pt(x, y + 0.2, z)} 0.4 0.3 0.4 0.1 24 force',
        f"particle minecraft:dust_plume {pt(x, y, z)} 0.3 0.2 0.3 0.02 10 force"]


# where each kind may be put on the island: pools of columns (stage x, z), by its own countries
near_wet = dilate(wet & (depth >= 2), 2)
SNOWY = SNOWZ
POOL = {}
for kind, spec in ANIM.items():
    where_, zs_ = spec["where"], np.isin(ZONE, zone_idx(spec["biomes"]))
    if where_ in ("land", "air"):
        m = zs_ & dry & ~NEAR_TREE & ~STREAM & (slope <= 3)
        if where_ == "land":
            m &= ~OPEN_VIEW
    elif where_ == "shore":
        m = dilate(zs_, 3) & dry & near_wet & ~NEAR_TREE
    else:
        m = zs_ & wet & (depth >= (5 if kind in ("dolphin", "squid", "glow_squid", "nautilus") else 2))
    cols = np.argwhere(m)
    if len(cols) == 0 and where_ == "water":                    # a water kind whose country has no water deep enough
        cols = np.argwhere(np.isin(ZONE, zone_idx(sorted(OCEANS))) & wet & (depth >= 5))
    POOL[kind] = [(int(i) - N, int(j) - N) for i, j in cols]
    if not POOL[kind]:
        print(f"  note: no place on the island for {kind} ({spec['biomes']})")


def creature_y(kind, spec, x, z):
    h = int(H[x + N, z + N])
    where_ = spec["where"]
    if where_ == "air":
        lo, hi = {"parrot": (16, 32), "bee": (3, 7), "bat": (4, 10)}.get(kind, (6, 14))
        return h + random.uniform(lo, hi)
    if where_ == "water":
        top = int(WAT[x + N, z + N]) if WAT[x + N, z + N] > h else SEA
        lo, hi = h + 1.3, top - 1.3
        if kind in ("axolotl", "tadpole"):
            return h + 1.1
        if kind == "dolphin":
            return max(lo, top - random.uniform(2, 4))
        return random.uniform(lo, hi) if hi > lo else lo
    return h + 1.05 + (0.3 if SNOWY[x + N, z + N] else 0.0)


def creature_nbt(kind, spec, x, z):
    zn_ = ZN[ZONE[x + N, z + N]]
    if zn_ in spec["by_biome"]:
        return spec["by_biome"][zn_]
    if spec.get("variants"):
        return random.choice(spec["variants"])
    return spec["nbt"]


def island_creatures(kind):
    """[(x, y, z, nbt)] for the whole count of one kind, in little herds, each in its own country."""
    spec, pool = ANIM[kind], POOL[kind]
    out = []
    if not pool:
        return out
    herd = 1 if kind in ("bat", "parrot", "bee") else (4 if spec["where"] in ("land", "water") else 2)
    centres = random.sample(pool, min(len(pool), math.ceil(spec["count"] / herd)))
    n = 0
    while n < spec["count"]:
        cx_, cz_ = centres[n % len(centres)]
        x, z = cx_, cz_
        if n >= len(centres):
            for _ in range(6):
                x, z = cx_ + random.randint(-5, 5), cz_ + random.randint(-5, 5)
                if 0 <= x + N <= 2 * N and 0 <= z + N <= 2 * N and (x, z) in POOLSET[kind]:
                    break
                x, z = cx_, cz_
        out.append((x + random.uniform(0.2, 0.8), creature_y(kind, spec, x, z), z + random.uniform(0.2, 0.8), creature_nbt(kind, spec, x, z)))
        n += 1
    return out


POOLSET = {k: set(v) for k, v in POOL.items()}
ISLAND = {k: island_creatures(k) for k in ANIM}


def place(name, x, z, look):
    wx, wz = wp(x + 0.5, z + 0.5)
    return name, {"x": round(wx, 1), "z": round(wz, 1), "look": look}


PLACES = {n: dict(zip(("x", "z", "look"), (round(wp(p["x"] + 0.5, p["z"] + 0.5)[0], 1), round(wp(p["x"] + 0.5, p["z"] + 0.5)[1], 1), p["look"])))
          for n, p in TER["places"].items()}
PLACES.update(dict([
    place("the clearing", 0, CLEAR_Z + 2, "the flat ground where you both first opened your eyes"),
    place("the meadow", 0, CLEAR_Z - 26, "the wide open grass between the clearing and the lake, where the creatures graze"),
    place("the lake", 0, LAKE_S + 2, "a wide still water in the middle of the land, ahead of where you woke; lilies float on it and reeds grow at its edge"),
    place("the near shore", 0, S0 - 4, "behind where you woke, where the land ends in pale sand and the great water begins"),
]))
VIEW = {}                                      # for the picture test: where to stand in each place (world x, y, z)
for _n, _p in TER["places"].items():
    _wx, _wz = wp(_p["x"] + 0.5, _p["z"] + 0.5)
    VIEW[_n] = [round(_wx, 1), int(max(H[_p["x"] + N, _p["z"] + N], WAT[_p["x"] + N, _p["z"] + N])) + 1, round(_wz, 1)]
VIEW["the lake shore"] = [round(wp(0.5, LAKE_S + 6.5)[0], 1), 64, 0.5]
json.dump(VIEW, open(os.path.join(ROOT, "work", "view_points.json"), "w"), indent=1)
json.dump({"kinds": KINDS,
           "look": {"whale": WHALE_LOOK, **{k: v["look"] for k, v in ANIM.items()}},
           "selector": {"whale": "@e[tag=gen.whale]", **{k: f"@e[type=minecraft:{k},tag=!gen.whale]" for k in ANIM}},
           "places": PLACES},
          open(os.path.join(ROOT, "companion", "creatures.json"), "w"), indent=1)

# the guaranteed cast near the camera: the meadow in front of the clearing, the lake shore, the clearing's edges
free_ = dry & ~DECO & ~NEAR_TREE
meadow = [(int(i) - N, int(j) - N) for i, j in np.argwhere(free_ & (np.abs(X) < 30) & (Z > CLEAR_Z - 40) & (Z < CLEAR_Z - 6) & (H >= SEA + 1) & (H <= 74))]
edges = [(int(i) - N, int(j) - N) for i, j in np.argwhere(
    free_ & (np.abs(X) > 12) & (np.abs(X) < 30) & (Z > CLEAR_Z - 4) & (Z < CLEAR_Z + 16) & (H <= 72))] or meadow
_ell = ((X - LAKE["cx"]) / LAKE["rx"]) ** 2 + ((Z - LAKE["cz"]) / LAKE["rz"]) ** 2
lake_shore = [(int(i) - N, int(j) - N) for i, j in np.argwhere(dry & (_ell > 1.0) & (_ell < 1.6) & (H <= 65) & (Z > LAKE["cz"]) & ~NEAR_TREE)] or meadow
lake_water = [(int(i) - N, int(j) - N) for i, j in np.argwhere((_ell < 0.5) & wet & (depth >= 3))] or meadow
for pool in (meadow, edges, lake_shore, lake_water):
    random.shuffle(pool)
_used = [0]


def spot(pool):
    _used[0] += 1
    x, z = pool[(_used[0] * 7) % len(pool)]
    return x + 0.5, int(H[x + N, z + N]) + 1, z + 0.5


# ---------------------------------------------------------------- the schedule
TIMING = {int(k): v for k, v in json.load(open(os.path.join(ROOT, "narration", "timing.json"))).items()}
T = lambda s: int(round(s * 20))
GAP = {2: 2.5, 3: 5.0, 5: 2.0, 7: 2.5, 9: 14.0, 10: 2.0, 11: 2.5, 12: 4.0, 13: 2.0, 16: 4.5, 19: 2.0,
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


def cost_of(c):
    if isinstance(c, tuple):
        return c[1]
    if c.startswith("fillbiome"):
        p = c.split()
        return 6.0 + 0.3 * (abs(int(p[4]) - int(p[1])) + 1) * (abs(int(p[5]) - int(p[2])) + 1) * (abs(int(p[6]) - int(p[3])) + 1) / 64.0
    if c.startswith("fill"):
        p = c.split()
        vol = (abs(int(p[4]) - int(p[1])) + 1) * (abs(int(p[5]) - int(p[2])) + 1) * (abs(int(p[6]) - int(p[3])) + 1)
        return 6.0 + 1.1 * vol
    if c.startswith("place feature"):
        return 25.0
    return 3.0


def spread(items, cap, limit=None):
    """Lay command lists onto ticks without ever putting more than `cap` units of work on one tick.
    items: [(earliest tick, [command or (command, cost)])] in order. Returns the last tick used."""
    cur, used = -1, 0.0
    for item in sorted(items, key=lambda it: it[0]):
        earliest, cmds = item[0], item[1]
        capi = item[2] if len(item) > 2 else cap          # an item may carry a cap of its own
        for c in cmds:
            w = cost_of(c)
            if cur < earliest:
                cur, used = earliest, 0.0
            elif used + w > capi and used > 0:
                cur, used = cur + 1, 0.0
            at(cur, c[0] if isinstance(c, tuple) else c)
            used += w
    if limit is not None and cur > limit:
        print(f"  WARNING: work runs to tick {cur}, past {limit} ({cur - limit} ticks late)")
    return cur


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


# ---- God: where he stands. High and to one side of the long view, so that the sun and the moon, which
# come up straight ahead, never pass behind him and the great mountain is not hidden. Chosen with
# the camera path below (see the angle report it prints).
GOD_SCALE = 0.95                                               # a wingspan of about 105 blocks
GOD_S = (-125.0, 185.0, 40.0)                                  # stage x, y, z
GOD_X, GOD_Z = wp(GOD_S[0], GOD_S[2])
GOD_Y = GOD_S[1]

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
orb_at = f"{GOD_X:.2f} {GOD_Y:.2f} {GOD_Z:.2f}"
# ---- God appears where the light gathers, grows with the light, and stays in the sky
GOD_END = tw(33, "he rested")
_cx, _cz = wp(0.5, S0 - 10)                                    # he turns his face towards the middle of where we watch from
_d = math.hypot(_cx - GOD_X, _cz - GOD_Z)
GOD_FACE = math.degrees(math.atan2(-(_cx - GOD_X) / _d, (_cz - GOD_Z) / _d))
at(ORB, god.summon(GOD_X, GOD_Y, GOD_Z, GOD_SCALE, GOD_FACE))
at(ORB + 3, god.appear(max(10, LIGHT + 24 - (ORB + 3)), GOD_SCALE))
for k, tick in enumerate(range(ORB, LIGHT, 2)):                # a gathering point of light, which needs no light to be seen
    r = 0.3 + 0.35 * k
    at(tick, f"particle minecraft:end_rod {orb_at} {r:.2f} {r:.2f} {r:.2f} 0.002 {30 + 14 * k} force")
sound(ORB, "minecraft:block.amethyst_block.resonate", 0.9, 0.5)
at(LIGHT, [f"particle minecraft:flash{{color:[1.0,1.0,0.9,1.0]}} {orb_at} 0 0 0 0 1 force",
           f"particle minecraft:end_rod {orb_at} 3 3 3 1.6 2200 force",
           f"particle minecraft:glow {orb_at} 8 8 8 0.5 500 force",
           f"particle minecraft:firework {orb_at} 2 2 2 0.9 400 force"])
sound(LIGHT, f"{NS}:sfx.light", 1.0)
sound(LIGHT, "minecraft:block.beacon.activate", 0.9, 0.7)
sound(LIGHT + 12, "minecraft:block.amethyst_block.chime", 1.0, 0.8)
music(LIGHT + 10, "light")
F0 = LIGHT + 26                                                # the growth is done: the figure turns without end
for k, tick in enumerate(range(F0, GOD_END, 40)):
    at(tick, f"function {NS}:god/f{k % (god.LOOP // 40)}")
for tick in range(F0, GOD_END, 6):
    at(tick, f"function {NS}:god/spark")
for v, phrase in ((6, "And God said"), (9, "And God said"), (11, "And God said"), (14, "And God said"), (20, "And God said"),
                  (24, "And God said"), (26, "And God said"), (29, "And God said")):
    at(tw(v, phrase) + 4, f"function {NS}:god/pulse")        # each time God speaks, the figure flares
at(LIGHT + 30, f"function {NS}:god/pulse")                     # (the first time was the light itself)
at(GOD_END, god.vanish(40))
at(GOD_END + 44, god.remove())
for g in range(god.LOOP // 40):
    fn(f"god/f{g}", god.frame(g * 40, GOD_SCALE, 40))
fn("god/spark", god.particles(GOD_X, GOD_Y, GOD_Z, GOD_SCALE, GOD_FACE))
fn("god/pulse", [f"particle minecraft:end_rod {orb_at} 9 9 9 0.5 500 force",
                 f"particle minecraft:glow {orb_at} 12 12 8 0.2 150 force",
                 f"particle minecraft:firework {orb_at} 4 4 4 0.3 60 force",
                 f"execute as @a at @s run playsound {NS}:sfx.light ambient @s ~ ~ ~ 0.22 1.3 0.22"])
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
RISE_END = E[9] + T(GAP[9]) - 24
for tick in range(STIR, RISE + 40, 5):
    at(tick, [f"particle minecraft:bubble_pop {pt(0, 63, S0 - 60)} 62 0.2 62 0.01 800 force",
              f"particle minecraft:splash {pt(0, 63.2, S0 - 60)} 60 0.3 60 0.2 700 force"])
sound(STIR, "minecraft:ambient.underwater.loop", 0.8, 0.8)
sound(RISE, f"{NS}:sfx.rise", 1.0)
sound(RISE, "minecraft:entity.warden.emerge", 0.9, 0.5)
sound(RISE + 70, "minecraft:entity.warden.dig", 0.9, 0.5)
# The land comes up layer by layer from y = 51 (below that it was laid when the world was made). The
# first twelve layers are the shelf under the sea and come quickly; the rest climb at an even pace.
rise_items = []
RISE_CAP, RISE_CAP_LOW = 33000.0, 22000.0
_stepB = max(1.0, (RISE_END - 60 - RISE) / max(1, HMAX - SEA))
surface = {y: np.argwhere((H >= y) & (H <= y + 2)) for y in range(SEA + 1, HMAX + 1)}
for y in range(BASE_TOP + 1, HMAX + 1):
    early = STIR + 10 + (y - BASE_TOP - 1) * 3 if y <= SEA else RISE + 10 + int((y - SEA - 1) * _stepB)
    cmds = list(RISE_LAYERS[y])
    sp = surface.get(y)
    if sp is not None and len(sp) and y > SEA:
        for i, j in sp[rng.choice(len(sp), min(5, len(sp)), replace=False)]:
            px, pz = wp(int(i) - N + 0.5, int(j) - N + 0.5)
            cmds.append(f"particle minecraft:cloud {px:.1f} {y + 1} {pz:.1f} 4 1 4 0.03 50 force")
            cmds.append(f"particle minecraft:dust_plume {px:.1f} {y + 1} {pz:.1f} 6 0.5 6 0.03 40 force")
    rise_items.append((early, cmds, RISE_CAP_LOW if y <= SEA else RISE_CAP))     # the layers under the sea cost more (light)
rise_last = spread(rise_items, RISE_CAP, RISE_END)
for k, y in enumerate(range(BASE_TOP + 1, HMAX + 1, 6)):
    sound(RISE + 10 + k * (RISE_END - RISE) // ((HMAX - BASE_TOP) // 6 + 1), "minecraft:entity.generic.splash", 0.6, 0.5)
sound(tc(10, 1), "minecraft:ambient.underwater.exit", 0.7, 0.7)
# the lakes and the rivers fill, the spring starts to run, the snow settles, the caves open
WATER_T = S[10] + 6
spread([(WATER_T + 2 * k, WATER_LAYERS[y]) for k, y in enumerate(sorted(WATER_LAYERS))], 15000.0)
_sx, _sz = wb(SPRING[0], SPRING[2])
at(tc(10, 1), [f"setblock {_sx} {SPRING[1]} {_sz} minecraft:water", f"particle minecraft:splash {_sx} {SPRING[1] + 1} {_sz} 0.5 0.5 0.5 0.2 60 force"])
SNOW_T = S[10] + 40
spread([(SNOW_T + k, SNOW_LAYER_CMDS[y]) for k, y in enumerate(sorted(SNOW_LAYER_CMDS))], 15000.0)
CAVE_T = S[10] + 70
spread([(CAVE_T, CAVE_CMDS)], 15000.0)
GREEN = tw(11, "grass")
WAVE_END = E[11] + T(GAP[11]) + 60
gstep = (WAVE_END - GREEN) / (NRINGS + 2)
sound(GREEN, f"{NS}:sfx.growth", 0.9)
wave_items = [(GREEN + int(k * gstep), WAVE[k]) for k in sorted(WAVE)]
plant_items = [(GREEN + int((k + 2) * gstep), plants[k]) for k in sorted(plants)]
for k in range(0, NRINGS, 6):
    sound(GREEN + int(k * gstep), "minecraft:block.grass.place", 0.7, 0.7)
spread(wave_items, 20000.0, WAVE_END + 40)
plant_last = spread(plant_items, 20000.0, WAVE_END + 120)


def grow(site):
    x, z, h, kind, _ = site
    bx, bz = wb(x, z)
    return [f"setblock {bx} {h + 1} {bz} minecraft:air", (f"place feature minecraft:{kind} {bx} {h + 1} {bz}", 120.0)]


T11a, T12b = tw(11, "the fruit tree"), E[12] + T(GAP[12]) - 20
tree_items = []
for k, site in enumerate(tree_sites):
    ring = int(RINGS[site[0] + N, site[1] + N])
    slot = T11a + (T12b - T11a) * k // len(tree_sites)
    tree_items.append((max(slot, GREEN + int((ring + 3) * gstep)), grow(site)))
tree_last = spread(tree_items, 20000.0, T12b + 60)
for k in range(0, T12b - T11a, 40):
    sound(T11a + k, "minecraft:item.bone_meal.use", 0.8, 0.7)
sound(tw(12, "and the tree yielding fruit"), f"{NS}:sfx.growth", 0.9, 0.9)
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
    a = random.uniform(-90, 90)
    at(tick, f"particle minecraft:end_rod {pt(a * 1.5, random.uniform(150, 190), random.uniform(-40, 220))} 0.2 0.2 0.2 0.6 14 force")
lapse(S[17], E[17] + 10, 67000, 73000)                      # they take up their paths: dawn
lapse(tc(18, 0), tc(18, 0, True), 73000, 97000, 73000)      # one whole day and night
lapse(tc(18, 1), E[18], 73000, 78000)
lapse(S[19], E[19] + 30, 78000, 102000, 78000)
bell(E[19])
# ---- the fifth day: the waters and the air
music(S[20], "waters")
SEA_BOX = lambda: (random.uniform(-24, 24), random.uniform(56, 61), random.uniform(S0 + 10, S0 + 30))
SWIM = tw(20, "the moving creature") - 10
FOWL = tw(20, "and fowl that may fly")
WHALES = tw(21, "great whales")
MOVETH = tw(21, "every living creature that moveth")
WINGED = tw(21, "and every winged fowl")
FILL, MULT = tw(22, "fill the waters"), tw(22, "and let fowl multiply")
air = lambda: (random.uniform(-26, 26), random.uniform(68, 80), random.uniform(S0 + 14, S0 + 26))


def drip(base, cmd_lists, per_tick=2):
    for i, cmds in enumerate(cmd_lists):
        at(base + i // per_tick, cmds)


# the creatures of the waters: everywhere in the seas, rivers and pools (half on each verse), and the
# guaranteed cast in front of the camera
NEAR_SEA = {"cod": 30, "salmon": 18, "tropical_fish": 36, "pufferfish": 12, "squid": 6, "glow_squid": 3, "nautilus": 4}
near_first, near_second = [], []
for kind, n in NEAR_SEA.items():
    for i in range(n):
        x, y, z = SEA_BOX()
        nbt = random.choice(ANIM[kind]["variants"]) if ANIM[kind].get("variants") else ANIM[kind]["nbt"]
        (near_first if i < n // 2 else near_second).append(
            [summon(kind, x, y if i < n // 2 else y - 3, z, nbt), f"particle minecraft:bubble {pt(x, y, z)} 0.3 0.3 0.3 0.05 12 force"]
            + ([f"particle minecraft:splash {pt(x, 63.2, z)} 0.3 0.1 0.3 0.1 8 force"] if i < n // 2 else []))
random.shuffle(near_first)
random.shuffle(near_second)
island_first, island_second = [], []
for kind, spec in ANIM.items():
    if spec["group"] != "sea" or kind == "dolphin":
        continue
    items = [[summon(kind, x, y, z, nbt)] for x, y, z, nbt in ISLAND[kind]]
    h = len(items) // 2
    island_first += items[:h]
    island_second += items[h:]
random.shuffle(island_first)
random.shuffle(island_second)
drip(SWIM, [c for pair in zip(near_first, island_first[:len(near_first)]) for c in pair] + island_first[len(near_first):], 3)
drip(MOVETH, [c for pair in zip(near_second, island_second[:len(near_second)]) for c in pair] + island_second[len(near_second):], 3)
for i in range(4):                                          # the leaping ones leap
    x, z = random.uniform(-16, 16), random.uniform(S0 + 12, S0 + 24)
    at(SWIM + 14 + i * 9, [summon("dolphin", x, 61, z, "Motion:[0.0d,0.75d,0.0d]"),
                           f"particle minecraft:splash {pt(x, 63.3, z)} 0.6 0.3 0.6 0.4 60 force"])
for i, (x, y, z, nbt) in enumerate(ISLAND["dolphin"]):
    at(SWIM + 30 + i * 6, summon("dolphin", x, y, z, nbt))
for i in range(10):                                         # and the lake has its own
    x, z = lake_water[i % len(lake_water)]
    at(SWIM + 20 + i * 5, [summon("salmon" if i % 2 else "cod", x + 0.5, 60.5, z + 0.5, 'type:"medium"' if i % 2 else ""),
                           f"particle minecraft:splash {pt(x + 0.5, 63.2, z + 0.5)} 0.3 0.1 0.3 0.1 10 force"])
sound(SWIM, "minecraft:entity.dolphin.splash", 0.8, 0.8)
sound(SWIM + 20, "minecraft:entity.dolphin.jump", 0.9, 1.0)
for i in range(12):
    x, y, z = air()
    at(FOWL + i * 4, appear("parrot", x, y, z, f"Variant:{i % 5}"))
sound(FOWL, f"{NS}:sfx.birds", 0.9)
sound(FOWL, "minecraft:entity.parrot.fly", 1.0, 1.0)
whale = lambda s: f'attributes:[{{id:"minecraft:scale",base:{s}}}]'
WHALE_TAGS = ("gen.made", "gen.whale")
at(WHALES, [summon("dolphin", -13, 54, S0 + 14, whale(9.0), WHALE_TAGS),
            summon("dolphin", 15, 53, S0 + 12, whale(7.0), WHALE_TAGS),
            f"particle minecraft:bubble {pt(0.5, 54, S0 + 13)} 10 3 4 0.1 200 force"])
sound(WHALES, f"{NS}:sfx.whale", 1.0)
sound(WHALES, "minecraft:entity.elder_guardian.ambient", 0.8, 0.5)
for i in range(3):
    at(MOVETH + 20 + i * 12, summon("dolphin", random.uniform(-16, 16), 57, random.uniform(S0 + 14, S0 + 26)))
# the fowl of the island: chickens, parrots and bats, in their own countries, spread over the three verses
fowl_all = []
for kind, spec in ANIM.items():
    if spec["group"] == "fowl":
        fowl_all += [appear(kind, x, y, z, nbt) for x, y, z, nbt in ISLAND[kind]]
random.shuffle(fowl_all)
for part, base in zip((fowl_all[0::3], fowl_all[1::3], fowl_all[2::3]), (FOWL + 20, WINGED + 10, MULT + 10)):
    drip(base, part, 2)
for i in range(8):
    x, z = edges[i % len(edges)]
    at(WINGED + 30 + i * 5, appear("chicken", x + 0.5, int(H[x + N, z + N]) + 1, z + 0.5, 'variant:"minecraft:temperate"'))
for i in range(6):
    x, y, z = air()
    at(WINGED + 30 + i * 5, appear("parrot", x, y, z, f"Variant:{i % 5}"))
for i in range(24):
    x, y, z = SEA_BOX()
    kind = random.choice(["cod", "tropical_fish", "salmon"])
    nbt = random.choice(ANIM[kind]["variants"]) if ANIM[kind].get("variants") else ANIM[kind]["nbt"]
    at(FILL + i * 2, summon(kind, x, y, z, nbt))
for i in range(8):
    x, y, z = air()
    at(MULT + i * 4, appear("parrot", x, y + 4, z - 20, f"Variant:{i % 5}"))
sound(MULT, "minecraft:entity.parrot.ambient", 1.0, 1.0)
lapse(S[23], E[23] + 30, 78000, 102000, 78000)
bell(E[23])
# ---- the sixth day: the beasts of the earth
music(S[24], "beasts")
NEAR_LAND = {"cow": 9, "sheep": 12, "pig": 7, "horse": 8, "donkey": 3, "rabbit": 12}   # the herd in the meadow
NEAR_POOL = {"frog": (lake_shore, 4), "turtle": (lake_shore, 3)}


def earth_group(group, half):
    """The creatures of a group for one of the two verses (0 or 1), each in its own country, plus the meadow herd."""
    out = []
    for kind, spec in ANIM.items():
        if spec["group"] != group:
            continue
        mine = ISLAND[kind]
        part = mine[: (len(mine) + 1) // 2] if half == 0 else mine[(len(mine) + 1) // 2:]
        out += [from_earth(kind, x, y, z, nbt) for x, y, z, nbt in part]
        for pool, n in ([(meadow, NEAR_LAND[kind])] if kind in NEAR_LAND else []) + ([NEAR_POOL[kind]] if kind in NEAR_POOL else []):
            for _ in range((n + 1) // 2 if half == 0 else n // 2):
                x, y, z = spot(pool)
                nb = random.choice(spec["variants"]) if spec.get("variants") else spec["nbt"]
                out.append(from_earth(kind, x, y + (2 if kind == "bee" else 0), z, nb))
    random.shuffle(out)
    return out


for v, order in ((24, [("cattle", "cattle", 0), ("creeping", "and creeping thing", 0), ("beast", "and beast of the earth", 0)]),
                 (25, [("beast", "the beast of the earth", 1), ("cattle", "and cattle after their kind", 1), ("creeping", "and every thing that creepeth", 1)])):
    for group, phrase, half in order:
        drip(tw(v, phrase), earth_group(group, half), 2)
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
    at(tw(28, "the fowl of the air") + i * 4, summon("parrot", x, y, z, f"Variant:{i % 5},Motion:[-0.5d,0.0d,0.0d]"))
at(tw(29, "every herb bearing seed"), ["give @a[tag=gen.human] minecraft:wheat_seeds 12"]
   + [f"particle minecraft:happy_villager {pt(0.5, 69.5, CLEAR_Z - 8)} 8 0.4 8 0 80 force"])
at(tw(29, "and every tree"), [f"particle minecraft:glow {pt(x + 0.5, h + 5, z + 0.5)} 2 2 2 0 40 force" for x, z, h, _, _ in tree_sites[:20]])
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
SEAZ = S0 + 52.5                    # the fish and the birds appear 25 to 40 blocks in front of this
cam_keys = [(0, CAM0_S), (LIFT, CAM0_S), (E[7] + 30, (0.5, 74, S0 + 56.5)),
            (RISE_END, (0.5, 74, S0 + 56.5)), (E[10], (0.5, 135, S0 + 40.5)),
            (S[11], (0.5, 135, S0 + 40.5)), (E[12] + 40, (0.5, 110, SEAZ)),
            (S[20] - 30, (0.5, 110, SEAZ)), (SWIM, (0.5, 69, SEAZ)),
            (S[21] - 6, (0.5, 69, SEAZ)), (WHALES - 4, (0.5, 57, SEAZ)),
            (WINGED, (0.5, 57, SEAZ)), (WINGED + 50, (0.5, 69, SEAZ)),
            (S[22], (0.5, 69, SEAZ)), (E[22], (0.5, 72, SEAZ)),
            (S[23], (0.5, 72, SEAZ)), (tw(24, "the living creature"), (0.5, 86, cz + 38)),
            (S[25], (0.5, 86, cz + 38)), (E[25], (0.5, 78, cz + 26)),
            (S[26] - 20, (0.5, 78, cz + 26)), (BEAM + 30, (0.5, 69.4, cz + 12)),
            (E[27] + 14, (0.5, 69.4, cz + 12)), (AWAKE, (0.5, 69.0, cz + 1.0))]
cam_path = {}
for (t0, p0), (t1, p1) in zip(cam_keys, cam_keys[1:]):
    assert t1 >= t0, (t0, t1)
    if p0 == p1:
        continue
    for tick in range(t0 + 1, t1 + 1):
        a = terrain.smooth((tick - t0) / (t1 - t0))
        x, y, z = (p0[i] + (p1[i] - p0[i]) * a for i in range(3))
        cam_path[tick] = (x, y, z)
        at(tick, f"tp @e[type=minecraft:marker,tag=gen.cam,limit=1] {-z:.3f} {y:.3f} {x:.3f}")
CAM0 = pt(*CAM0_S)
# the camera must never be inside the ground or a tree (the player's eyes are 1.62 above the marker)
tree_cols = {(x, z) for x, z, *_ in tree_sites}
for tick, (x, y, z) in cam_path.items():
    if tick < RISE_END:
        continue                                              # before the land is up there is only sea
    ix, iz = int(math.floor(x)) + N, int(math.floor(z)) + N
    if 0 <= ix <= 2 * N and 0 <= iz <= 2 * N:
        top = max(H[ix, iz], WAT[ix, iz])
        assert y + 1.62 > top + 1.3, (tick, x, y, z, top)
        assert not any((int(math.floor(x)) + a, int(math.floor(z)) + b) in tree_cols for a in range(-4, 5) for b in range(-4, 5)), (tick, x, z)
print("God's direction from the camera keys (azimuth off the line of sight, elevation of his centre):")
for tick, (px, py, pz) in cam_keys:
    d_ = math.hypot(GOD_S[0] - px, GOD_S[2] - pz)
    print(f"  tick {tick:5d} cam z={pz:6.1f} y={py:5.1f}  azimuth {math.degrees(math.atan2(GOD_S[0] - px, pz - GOD_S[2])):6.1f}  "
          f"elevation {math.degrees(math.atan2(GOD_S[1] - (py + 1.6), d_)):5.1f}  distance {math.hypot(d_, GOD_S[1] - py):5.0f}")

# ---------------------------------------------------------------- timeline function
BUCKET = 64
for tick in sorted(cues):
    fn(f"cue/t{tick}", cues[tick])
    fn(f"tl/{tick // BUCKET}", f"execute if score #t gen matches {tick} run function {NS}:cue/t{tick}")
for b in sorted({tick // BUCKET for tick in cues}):
    fn("timeline", f"execute if score #t gen matches {b * BUCKET}..{b * BUCKET + BUCKET - 1} run function {NS}:tl/{b}")

# ---------------------------------------------------------------- fixed functions
lx, ly, lz = LOBBY
text = lambda x, y, z, s, colour, scale: (
    f'summon minecraft:text_display {x} {y} {z} {{Tags:["gen.lobbytext"],billboard:"center",background:0,'
    f'brightness:{{sky:15,block:15}},text:{{text:"{s}",color:"{colour}"}},'
    f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[{scale}f,{scale}f,{scale}f],right_rotation:[0f,0f,0f,1f]}}}}')
fn("load", ["scoreboard objectives add gen dummy",
            f"execute unless score #phase gen matches 0.. run function {NS}:setup"])
# the island is made once, when the world is made: first load every chunk it will stand in (forceload takes at
# most 256 chunks at a time), then lay the hidden base and the biomes a few at a time
TILES = [(a, b) for a in ((-352, -97), (-96, 159), (160, 351)) for b in ((-352, -97), (-96, 159), (160, 351))]
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
   + [f"time of {NS}:cut set 0", f"time of {NS}:cut pause", f"{DAY} set 6000", f"{DAY} pause"]
   + [f"forceload add {lx - 8} {lz - 8} {lx + 10} {lz + 8}",
      f"setworldspawn {lx - 3} {ly} {lz}", f"schedule function {NS}:setup2 60t", f"schedule function {NS}:fl0 20t"])
# a tile of chunks at a time (generating all 1940 at once stalls the server for six seconds), then the base in
# batches of about 25 milliseconds of work
for i, ((xa, xb), (za, zb)) in enumerate(TILES):
    fn(f"fl{i}", [f"forceload add {xa} {za} {xb} {zb}",
                  f"schedule function {NS}:{'fl' + str(i + 1) if i + 1 < len(TILES) else 'setup_t0'} {12 if i + 1 < len(TILES) else 100}t"])
SETUP_CMDS = base_cmds + biome_cmds
_batches, _cur, _used = [], [], 0.0
for c in SETUP_CMDS:
    w = cost_of(c)
    if _cur and _used + w > 25000.0:
        _batches.append(_cur)
        _cur, _used = [], 0.0
    _cur.append(c)
    _used += w
_batches.append(_cur)
for i, ch in enumerate(_batches):
    fn(f"setup_t{i}", ch + ([f"schedule function {NS}:setup_t{i + 1} 1t"] if i + 1 < len(_batches) else []))
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
             "kill @e[type=minecraft:item_display,tag=gen.god]",
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
cwx, cwz = wp(0.5, CLEAR_Z)
fn("free", ["scoreboard players set #phase gen 2", "scoreboard players set #cmode gen 1",
            "kill @e[type=minecraft:item_display,tag=gen.god]",
            "execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base reset",
            "execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base reset",
            f"{DAY} rate 1", f"{DAY} resume", "forceload remove all", f"forceload add {int(cwx) - 40} {int(cwz) - 40} {int(cwx) + 40} {int(cwz) + 40}",
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
write(f"data/{NS}/tags/entity_type/creature.json", {"values": [f"minecraft:{k}" for k in ANIM]})
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
size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
n_ani = sum(len(v) for v in ISLAND.values())
print(f"intro {END / 20 / 60:.1f} min ({END} ticks), {len(cues)} cue ticks, {ncmd} commands, datapack {size / 1e6:.1f} MB, island top y={HMAX}")
print(f"  base {len(base_cmds)} + biomes {len(biome_cmds)} setup commands; rise {sum(len(v) for v in RISE_LAYERS.values())} fills over layers {BASE_TOP + 1}..{HMAX}, "
      f"water {sum(len(v) for v in WATER_LAYERS.values())}, snow {sum(len(v) for v in SNOW_LAYER_CMDS.values())} ({SNOW_COLS} columns), caves {len(CAVE_CMDS)}")
print(f"  green wave {sum(len(v) for v in WAVE.values())} fills in {NRINGS} rings, ground cover {sum(len(v) for v in plants.values())}, {len(tree_sites)} trees")
print(f"  rise runs RISE={RISE} to tick {rise_last} (limit {RISE_END}); plants to {plant_last}; trees to {tree_last} (limit {T12b}); "
      f"{n_ani} island creatures + the guaranteed cast")
print("music:", [(s["name"], s["seconds"]) for s in sections])
