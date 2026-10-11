"""Procedural terrain for Eden, the big island, in "stage" coordinates.

    python tools\\terrain.py --preview work\\terrain_preview.png

Arrays are indexed [x + N, z + N] with N = 340 (681 x 681).  The viewer floats over the sea at +z and looks
toward -z, so +z is "near / south", -z is "far / north", -x is "left / west", +x is "right / east".
Heights are Minecraft y.  SEA = 62 is the top water block, FLOOR = 42 is the top of the flat sea bed.

    t = build(seed)        -> dict (see build() for the keys)
    validate(t)            -> list of human readable problems (empty when every constraint holds)

Method, in order (each step is a function below):
  1. a land field L (positive inland) from a calm circle plus warped noise and bays, then islets;
  2. a zone map from hand placed seeds, warped Voronoi style, laid out by climate (cold north, dry west,
     wet hot east, temperate south) -- every zone has a terrain recipe and the recipes are blended;
  3. heights = recipe blend + the great range (soft union of a cone and ridged spines) + the stage features
     (sand beach, clearing, meadow, lake, the stream down the near face of the great mountain);
  4. rivers follow the drainage of the terrain (priority-flood routing, steepest descent from valley heads in
     the mountains) as chains of level reaches that step down one block at a time; elevated lakes sit on the
     rivers (and a few tarns on the high ground) with level water and banks all round; sea level lakes and
     swamp pools are hollows whose water the rising land leaves behind;
  5. zones are finished from what the terrain did (height bands, shores, rivers, sea by climate);
  6. caves are wormed into hillsides, keeping clear of water, the clearing and the stage corridor;
  7. places (landmarks) are picked from the zones and features; validate() re-checks every rule.
Everything is deterministic for a given seed (the zone/terrain tuning was done on the default seed 31; other
seeds build fine but may miss a minimum area).  Needs numpy only (Pillow for the preview).
"""
import argparse
import heapq
import math
import os
import sys
import time

import numpy as np

N, SEA, FLOOR = 340, 62, 42
W = 2 * N + 1
S0_DESIGN = 270                       # the shore on the +z axis; the actual value is measured from H
CLEAR_R_IN, CLEAR_R_OUT, CLEAR_Y = 9, 18, 68
LAKE_CX, LAKE_CZ, LAKE_RX, LAKE_RZ = 0, 100, 40, 25
PEAK_X, PEAK_Z, PEAK_Y = 0, -25, 182

ZONES = ["plains", "sunflower_plains", "meadow", "forest", "flower_forest", "birch_forest",
         "old_growth_birch_forest", "dark_forest", "dappled_forest", "pale_garden", "cherry_grove", "taiga",
         "old_growth_pine_taiga", "old_growth_spruce_taiga", "snowy_taiga", "snowy_plains", "ice_spikes", "grove",
         "snowy_slopes", "frozen_peaks", "jagged_peaks", "stony_peaks", "windswept_hills", "windswept_forest",
         "windswept_gravelly_hills", "savanna", "savanna_plateau", "windswept_savanna", "desert", "badlands",
         "wooded_badlands", "eroded_badlands", "jungle", "sparse_jungle", "bamboo_jungle", "swamp",
         "mangrove_swamp", "mushroom_fields", "beach", "snowy_beach", "stony_shore", "river", "frozen_river",
         "warm_ocean", "lukewarm_ocean", "ocean", "cold_ocean", "frozen_ocean"]
ZI = {z: i for i, z in enumerate(ZONES)}
THIN = {"beach", "snowy_beach", "stony_shore", "river", "frozen_river"}   # allowed to be narrow
MIN_AREA, MIN_THIN = 1500, 120
COLD = {"snowy_taiga", "snowy_plains", "ice_spikes", "snowy_slopes", "frozen_peaks", "jagged_peaks", "grove",
        "snowy_beach", "frozen_river", "frozen_ocean"}

# ------------------------------------------------------------------ small numeric helpers


def smooth(a):
    a = np.clip(a, 0.0, 1.0)
    return a * a * (3 - 2 * a)


def lerp(a, b, t):
    return a + (b - a) * t


_GRID = None


def grid():
    global _GRID
    if _GRID is None:
        xs = np.arange(-N, N + 1, dtype=np.float32)
        _GRID = np.meshgrid(xs, xs, indexing="ij")
    return _GRID


FFT = 1024
_K = None


def _kgrid():
    global _K
    if _K is None:
        f = np.fft.fftfreq(FFT)[:, None]
        g = np.fft.rfftfreq(FFT)[None, :]
        _K = np.hypot(f, g).astype(np.float32)
        _K[0, 0] = 1.0
    return _K


def fnoise(rng, lam_max, lam_min, beta=2.6):
    """Isotropic fractal noise, unit std: white noise shaped in the frequency domain so that only wavelengths
    between lam_min and lam_max (blocks) survive, with power ~ k^-beta (bigger beta = smoother)."""
    k = _kgrid()
    amp = k ** (-beta / 2.0)
    amp = amp / (1.0 + (1.0 / (k * lam_max)) ** 4)
    amp = amp / (1.0 + (k * lam_min) ** 4)
    amp[0, 0] = 0.0
    f = np.fft.rfft2(rng.standard_normal((FFT, FFT)).astype(np.float32)) * amp
    a = np.fft.irfft2(f, s=(FFT, FFT))
    ox, oz = int(rng.integers(0, FFT - W)), int(rng.integers(0, FFT - W))
    a = a[ox:ox + W, oz:oz + W]
    return ((a - a.mean()) / a.std()).astype(np.float32)


def ridged(rng, lam_max, octaves=5, gain=2.2):
    """Ridged multifractal in [0, 1]: sharp crests where band-limited noise crosses zero; each octave is
    weighted by the previous one so that the detail clings to the ridges and the flats stay smooth."""
    out, w, amp, tot, lam = 0.0, 1.0, 1.0, 0.0, float(lam_max)
    for _ in range(octaves):
        n = fnoise(rng, lam, lam * 0.5, 1.0)
        r = 1.0 - np.minimum(np.abs(n) / 1.7, 1.0)
        r = r * r * w
        w = np.clip(r * gain, 0.0, 1.0)
        out = out + r * amp
        tot += amp
        amp *= 0.55
        lam *= 0.5
    out = out / tot
    lo, hi = np.percentile(out, 3), np.percentile(out, 99.5)
    return np.clip((out - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def _nice(n):
    while True:
        m = n
        for p in (2, 3, 5):
            while m % p == 0:
                m //= p
        if m == 1:
            return n
        n += 1


def blur(a, sigma):
    """Gaussian blur by FFT (edges replicated)."""
    p = int(4 * sigma) + 1
    a = np.pad(np.asarray(a, dtype=np.float32), p, mode="edge")
    h, w = a.shape
    hh, ww = _nice(h), _nice(w)
    f = np.fft.rfft2(a, s=(hh, ww))
    fx = np.fft.fftfreq(hh)[:, None]
    fz = np.fft.rfftfreq(ww)[None, :]
    f = f * np.exp(-2 * (math.pi * sigma) ** 2 * (fx * fx + fz * fz))
    return np.fft.irfft2(f, s=(hh, ww))[p:p + h - 2 * p, p:p + w - 2 * p].astype(np.float32)


def sample(a, xs, zs):
    """Bilinear sample of a [x+N, z+N] array at stage coordinates."""
    fx = np.clip(xs + N, 0, W - 1.001)
    fz = np.clip(zs + N, 0, W - 1.001)
    i, j = fx.astype(np.int32), fz.astype(np.int32)
    tx, tz = fx - i, fz - j
    return (a[i, j] * (1 - tx) * (1 - tz) + a[i + 1, j] * tx * (1 - tz)
            + a[i, j + 1] * (1 - tx) * tz + a[i + 1, j + 1] * tx * tz)


def edt(mask, maxd=64):
    """Euclidean distance from every cell to the nearest True cell of mask, capped at maxd (exact below the cap)."""
    big = float(maxd + 1)
    g = np.where(mask, 0.0, big).astype(np.float32)
    for i in range(1, g.shape[0]):
        np.minimum(g[i], g[i - 1] + 1, out=g[i])
    for i in range(g.shape[0] - 2, -1, -1):
        np.minimum(g[i], g[i + 1] + 1, out=g[i])
    g2 = np.minimum(g, big) ** 2
    out = g2.copy()
    for d in range(1, maxd + 1):
        a = g2[:, d:] + d * d
        np.minimum(out[:, :-d], a, out=out[:, :-d])
        b = g2[:, :-d] + d * d
        np.minimum(out[:, d:], b, out=out[:, d:])
    return np.minimum(np.sqrt(out), big)


def label(a):
    """4-connected components of equal value.  Returns (labels int32, number of labels, value of each label)."""
    h, w = a.shape
    starts, ends, rows, vals = [], [], [], []
    for i in range(h):
        row = a[i]
        cut = np.flatnonzero(row[1:] != row[:-1]) + 1
        s = np.concatenate(([0], cut))
        e = np.concatenate((cut, [w])) - 1
        starts.append(s.tolist())
        ends.append(e.tolist())
        vals.append(row[s].tolist())
        rows.append(len(s))
    base = np.concatenate(([0], np.cumsum(rows)))
    parent = list(range(int(base[-1])))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(1, h):
        sa, ea, va = starts[i - 1], ends[i - 1], vals[i - 1]
        sb, eb, vb = starts[i], ends[i], vals[i]
        p = q = 0
        while p < len(sa) and q < len(sb):
            if va[p] == vb[q] and max(sa[p], sb[q]) <= min(ea[p], eb[q]):
                ra, rb = find(base[i - 1] + p), find(base[i] + q)
                if ra != rb:
                    parent[rb] = ra
            if ea[p] < eb[q]:
                p += 1
            else:
                q += 1
    roots = {}
    out = np.zeros((h, w), dtype=np.int32)
    rv = []
    for i in range(h):
        for r in range(rows[i]):
            root = find(base[i] + r)
            if root not in roots:
                roots[root] = len(roots)
                rv.append(vals[i][r])
            out[i, starts[i][r]:ends[i][r] + 1] = roots[root]
    return out, len(roots), np.array(rv)


def components(mask):
    """Label a boolean mask: (labels with 0 = background and 1.. = components, sizes[1..])."""
    lab, n, v = label(mask.astype(np.uint8))
    keep = np.flatnonzero(v == 1)
    remap = np.zeros(n, dtype=np.int32)
    remap[keep] = np.arange(1, len(keep) + 1)
    lab = remap[lab]
    sizes = np.bincount(lab.ravel(), minlength=len(keep) + 1)
    return lab, sizes


# ------------------------------------------------------------------ layout tables

# climate layout: (zone, x, z, weight).  A column belongs to the seed with the smallest warped distance / weight.
LAND_SEEDS = [
    # temperate centre and south
    ("plains", 0, 190, 1.7), ("plains", 0, 125, 1.4),
    ("sunflower_plains", -95, 195, 1.05),
    ("meadow", 0, 40, 0.8),
    ("flower_forest", 100, 105, 0.85),
    ("cherry_grove", -92, 115, 1.0),
    ("forest", 80, 30, 0.85),
    ("birch_forest", -90, 45, 0.85),
    ("old_growth_birch_forest", 118, -22, 0.8),
    ("dark_forest", 95, 185, 1.25),
    ("dappled_forest", -105, -15, 0.9),
    ("pale_garden", -130, 62, 1.4),
    # the cold north
    ("snowy_plains", -90, -235, 1.0), ("snowy_plains", 20, -270, 0.8),
    ("ice_spikes", -185, -205, 0.85),
    ("snowy_taiga", 100, -240, 0.8), ("snowy_taiga", -45, -150, 0.8),
    ("taiga", 175, -185, 1.35),
    ("old_growth_pine_taiga", 215, -115, 1.0),
    ("old_growth_spruce_taiga", 135, -150, 0.6),
    # windswept hills between the cold and the dry
    ("windswept_gravelly_hills", -150, -125, 0.85),
    ("windswept_hills", -118, -62, 0.8),
    ("windswept_forest", -170, -75, 1.0),
    # the dry west
    ("eroded_badlands", -245, -70, 0.85), ("badlands", -215, -12, 0.9), ("wooded_badlands", -172, -22, 0.7),
    ("desert", -225, 70, 1.3),
    ("savanna", -225, 100, 1.35), ("savanna_plateau", -150, 125, 0.9), ("windswept_savanna", -200, 178, 0.75),
    # the hot wet east
    ("jungle", 200, -70, 0.95), ("sparse_jungle", 150, -22, 1.0), ("bamboo_jungle", 235, -5, 0.85),
    ("swamp", 182, 88, 0.9), ("mangrove_swamp", 242, 72, 0.85),
]

SEA_SEEDS = [
    ("frozen_ocean", 0, -345, 1.0), ("frozen_ocean", -150, -335, 1.0), ("frozen_ocean", 150, -335, 1.0),
    ("cold_ocean", -330, -230, 1.0), ("cold_ocean", 330, -230, 1.0), ("cold_ocean", -240, -330, 0.8),
    ("ocean", -340, -90, 0.9), ("ocean", 0, 340, 1.1), ("ocean", -130, 335, 0.9), ("ocean", 130, 335, 0.9),
    ("lukewarm_ocean", -340, 30, 0.8), ("lukewarm_ocean", 340, -80, 0.8), ("lukewarm_ocean", 250, 320, 0.8),
    ("warm_ocean", 340, 110, 0.9), ("warm_ocean", -300, 180, 0.9), ("lukewarm_ocean", -250, 300, 0.7),
]

# terrain recipe for each zone:
#   base, aL, aM, aH (std of low / mid / high frequency noise), aR (ridged), aD (dunes), aMesa (terraces),
#   aP (plateau), cliff (1 = the coast beside it may be cliffs)
RECIPE_KEYS = ("base", "aL", "aM", "aH", "aR", "aD", "aMesa", "aP", "cliff")
RECIPE = {
    "plains": (67, 2.6, 1.6, .4, 0, 0, 0, 0, 0),
    "sunflower_plains": (67.5, 2.4, 1.4, .4, 0, 0, 0, 0, 0),
    "meadow": (70, 4.5, 2, .5, 0, 0, 0, 0, 0),
    "forest": (71, 5.5, 3, .6, 3, 0, 0, 0, 0),
    "flower_forest": (70, 4.5, 2.5, .6, 0, 0, 0, 0, 0),
    "birch_forest": (71, 5, 2.8, .6, 3, 0, 0, 0, 0),
    "old_growth_birch_forest": (73, 6, 3.2, .7, 5, 0, 0, 0, 0),
    "dark_forest": (72, 5.5, 3, .6, 6, 0, 0, 0, 0),
    "dappled_forest": (73, 6, 3, .6, 5, 0, 0, 0, 0),
    "pale_garden": (69, 3.2, 2, .5, 0, 0, 0, 0, 0),
    "cherry_grove": (80, 7, 3.5, .5, 12, 0, 0, 0, 0),
    "taiga": (74, 6.5, 3, .6, 8, 0, 0, 0, 1),
    "old_growth_pine_taiga": (75, 7, 3.5, .6, 10, 0, 0, 0, 1),
    "old_growth_spruce_taiga": (75, 7, 3.5, .6, 10, 0, 0, 0, 1),
    "snowy_taiga": (74, 6.5, 3, .6, 9, 0, 0, 0, 1),
    "snowy_plains": (68, 3.2, 1.7, .4, 0, 0, 0, 0, 1),
    "ice_spikes": (67, 1.2, 1.0, .3, 0, 0, 0, 0, 0),
    "windswept_hills": (92, 12, 6, 1.2, 28, 0, 0, 0, 1),
    "windswept_forest": (90, 11, 6, 1.1, 25, 0, 0, 0, 1),
    "windswept_gravelly_hills": (98, 12, 7, 1.2, 32, 0, 0, 0, 1),
    "savanna": (68, 3, 2, .5, 0, 0, 0, 0, 0),
    "savanna_plateau": (70, 3, 2, .5, 0, 0, 0, 22, 1),
    "windswept_savanna": (84, 9, 5, 1, 18, 0, 0, 0, 1),
    "desert": (66, 3, 1, .3, 0, 11, 0, 0, 0),
    "badlands": (66, 2, 1.5, .4, 0, 0, 52, 0, 1),
    "wooded_badlands": (74, 2.5, 1.5, .4, 0, 0, 20, 16, 1),
    "eroded_badlands": (66, 2, 1.5, .4, 18, 0, 62, 0, 1),
    "jungle": (74, 8, 5, .8, 12, 0, 0, 0, 0),
    "sparse_jungle": (72, 7, 4, .7, 9, 0, 0, 0, 0),
    "bamboo_jungle": (76, 9, 5, .8, 14, 0, 0, 0, 0),
    "swamp": (62.7, 0.4, 0.7, .25, 0, 0, 0, 0, 0),
    "mangrove_swamp": (62.5, 0.3, 0.6, .25, 0, 0, 0, 0, 0),
    "mushroom_fields": (68, 5, 2.5, .4, 0, 0, 0, 0, 0),
}

# the great range: spines of high ground radiating from the great mountain: (points, uplift at start, at end)
SPINES = [
    ([(-30, -40), (-82, -72), (-140, -110), (-205, -165), (-245, -225)], 80, 52),     # west
    ([(30, -40), (88, -66), (148, -108), (205, -172), (238, -240)], 80, 52),          # east
    ([(0, -60), (-8, -110), (18, -170), (-30, -240), (-8, -295)], 94, 58),            # north
    ([(-140, -110), (-118, -185), (-135, -250)], 64, 36),                             # branch NW
    ([(148, -108), (122, -190), (150, -262)], 62, 36),                                # branch NE
    ([(-82, -72), (-102, -10), (-112, 48)], 38, 12),                                  # SW spur
    ([(88, -66), (112, -8), (118, 46)], 38, 12),                                      # SE spur
]


# ------------------------------------------------------------------ 1. land and sea


def land_field(rng, X, Z):
    """L > 0 on land, ~ signed distance (in blocks) to the coast.  The +z axis near the stage shore is kept as
    a calm circle so that the shore there is exactly at z = S0_DESIGN."""
    R = np.hypot(X, Z)
    nn = 0.85 * fnoise(rng, 420, 100, 2.4) + 0.3 * fnoise(rng, 140, 40, 2.2)
    mask = smooth((np.hypot(X, Z - S0_DESIGN) - 40) / 120.0)
    A = 38.0
    L = S0_DESIGN - R + mask * A * (np.tanh(0.9 * nn) - 0.10)
    # two bays that leave room for islets; a long headland on the west is the noise's job
    for bx, bz, bs, ba in ((165, 175, 70, 62), (-150, 215, 60, 40), (232, -125, 55, 28)):
        L = L - ba * np.exp(-((X - bx) ** 2 + (Z - bz) ** 2) / (2.0 * bs * bs))
    return np.minimum(L, 312 - R).astype(np.float32)


def distance_estimate(L):
    """First order signed distance L/|grad L| (exact near the coast, a little generous far from it)."""
    gx, gz = np.gradient(L)
    inland = L / np.clip(np.hypot(gx, gz), 0.6, 2.0)
    return np.where(L > 0, inland, -edt(L > 0, 70)).astype(np.float32)   # at sea: the exact distance


def place_islets(rng, L, X, Z):
    """Add islets to L.  Returns new L, list of (cx, cz, r), index of the mushroom islet."""
    R = np.hypot(X, Z)
    islets = []
    sizes = [30, 16, 13, 11, 9, 14, 10]
    for k, r in enumerate(sizes):
        dmain = edt(L > 0, 80)
        ok = (dmain > r + (22 if k == 0 else 14)) & (R + r + 8 < 316) & (np.hypot(X, Z - S0_DESIGN) > 120 + r)
        for (cx, cz, r2) in islets:
            ok &= np.hypot(X - cx, Z - cz) > r + r2 + 14
        if k == 0:     # the strange island: aim at the south east, otherwise anywhere there is room
            score = np.where(ok, -np.hypot(X - 190, Z - 190) + 0.4 * dmain, -1e9)
        else:
            score = np.where(ok, rng.random(L.shape) * 100 - np.abs(dmain - (r + 20)), -1e9)
        if score.max() < -1e8:
            continue
        i, j = np.unravel_index(int(np.argmax(score)), score.shape)
        cx, cz = int(X[i, j]), int(Z[i, j])
        islets.append((cx, cz, r))
        rough = fnoise(rng, 40, 8, 2.0)
        Li = r + 0.22 * r * rough - np.hypot(X - cx, Z - cz) * (1 + 0.0 * rough)
        L = np.maximum(L, Li.astype(np.float32))
    return L, islets


def voronoi(seeds, X, Z, rng, warp=28.0, jitter=12.0, bonus=None):
    """Index (into seeds) of the nearest seed by warped distance / weight."""
    wx = X + warp * fnoise(rng, 300, 90, 2.4)
    wz = Z + warp * fnoise(rng, 300, 90, 2.4)
    jit = [fnoise(rng, 120, 40, 2.2) for _ in range(3)]
    best = np.full(X.shape, 1e9, dtype=np.float32)
    idx = np.zeros(X.shape, dtype=np.int16)
    for k, (_, sx, sz, w) in enumerate(seeds):
        d = np.hypot(wx - sx, wz - sz) / w + jitter * jit[k % 3]
        if bonus is not None and seeds[k][0] in bonus:
            d = d - bonus[seeds[k][0]]
        m = d < best
        best = np.where(m, d, best)
        idx = np.where(m, k, idx)
    return idx


# ------------------------------------------------------------------ 2. height synthesis


def recipe_maps(zone_map, sigma=14.0):
    """Blend the zone recipes into smooth parameter fields (so that a desert melts into a savanna)."""
    table = np.zeros((len(ZONES), len(RECIPE_KEYS)), dtype=np.float32)
    default = np.array(RECIPE["snowy_taiga"], dtype=np.float32)       # zones without a recipe (peaks etc.)
    for z in ZONES:
        table[ZI[z]] = RECIPE.get(z, default)
    return {k: blur(table[zone_map, i], sigma) for i, k in enumerate(RECIPE_KEYS)}


def make_noise(rng, X, Z):
    """The shared noise bank: everything is warped by one displacement so features do not line up on a grid."""
    wx = 13.0 * fnoise(rng, 320, 110, 2.4)
    wz = 13.0 * fnoise(rng, 320, 110, 2.4)

    def warped(a):
        return sample(a, X + wx, Z + wz)

    nb = {"warp": (wx, wz)}
    nb["L"] = warped(fnoise(rng, 280, 90, 2.6))
    nb["M"] = warped(fnoise(rng, 95, 28, 2.4))
    nb["H"] = fnoise(rng, 30, 8, 2.0)
    nb["R"] = blur(warped(ridged(rng, 150, 5)), 0.9)
    nb["Rf"] = ridged(rng, 70, 4)
    # dunes: crescent ridges with a gentle slope up-wind and a steep slip face; flat pans where m is low
    phi = math.radians(28)
    ph = (X * math.cos(phi) + Z * math.sin(phi)) / 27.0 + 0.55 * fnoise(rng, 130, 40, 2.4) + 0.1 * nb["M"]
    u = ph - np.floor(ph)
    v = np.where(u < 0.7, u / 0.7, (1 - u) / 0.3)
    m = smooth((fnoise(rng, 320, 100, 2.6) + 0.35) / 1.1)
    nb["D"] = (v * v * (3 - 2 * v) * (0.55 + 0.45 * m) * m).astype(np.float32)
    # mesas: terraced noise -- flat tops, sharp steps
    s = np.clip((fnoise(rng, 190, 45, 2.6) + 1.5) / 3.0, 0, 1) * 4.0
    f = np.floor(s)
    fr = s - f
    nb["Mesa"] = ((f + smooth((fr - 0.62) / 0.05)) / 4.0 + 0.02 * fr).astype(np.float32)
    nb["Plat"] = smooth((fnoise(rng, 240, 70, 2.8) - 0.1) / 0.16)
    nb["pool"] = fnoise(rng, 70, 16, 2.4)
    nb["cliff"] = fnoise(rng, 320, 60, 2.2)
    nb["lake"] = fnoise(rng, 80, 20, 2.2)
    return nb


def seg_dist(X, Z, ax, az, bx, bz):
    abx, abz = bx - ax, bz - az
    t = np.clip(((X - ax) * abx + (Z - az) * abz) / (abx * abx + abz * abz), 0, 1)
    return np.hypot(X - (ax + t * abx), Z - (az + t * abz)), t


def mountain_uplift(rng, X, Z):
    """Height above the local ground for the great range (before the ridged detail)."""
    wx = 13.0 * fnoise(rng, 260, 100, 2.4)
    wz = 13.0 * fnoise(rng, 260, 100, 2.4)
    Xw, Zw = X + wx, Z + wz
    d = np.hypot(Xw - PEAK_X, Zw - PEAK_Z)
    parts = [112.0 * np.clip(1 - d / 115.0, 0, 1) ** 2.0]
    for pts, u0, u1 in SPINES:
        seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        total = sum(seg)
        best = np.full(X.shape, 1e9, dtype=np.float32)
        spos = np.zeros(X.shape, dtype=np.float32)
        acc = 0.0
        for (a, b), sl in zip(zip(pts, pts[1:]), seg):
            dd, t = seg_dist(Xw, Zw, a[0], a[1], b[0], b[1])
            m = dd < best
            best = np.where(m, dd, best)
            spos = np.where(m, (acc + t * sl) / total, spos)
            acc += sl
        ph1, ph2 = rng.random(2) * 6.28
        hgt = u0 + (u1 - u0) * spos
        hgt = hgt * (1 + 0.20 * np.sin(2 * np.pi * 3.1 * spos + ph1) + 0.10 * np.sin(2 * np.pi * 7.3 * spos + ph2))
        sig = 23.0 - 8.0 * spos
        parts.append(hgt * np.exp(-0.5 * (best / sig) ** 2))
    k = 8.0
    mx = np.maximum.reduce(parts)
    return mx + k * np.log(sum(np.exp((p - mx) / k) for p in parts))


def build_heights(rng, X, Z, L, Ld, zone_map, nb):
    """Float heights for the whole stage: land (with beaches, cliffs, the great range, the stage features) and sea floor."""
    rm = recipe_maps(zone_map)
    nL, nM, nH, Rg = nb["L"], nb["M"], nb["H"], nb["R"]
    hint = (rm["base"] + rm["aL"] * nL + rm["aM"] * nM + rm["aH"] * nH + rm["aR"] * Rg + rm["aD"] * nb["D"]
            + rm["aMesa"] * nb["Mesa"] + rm["aP"] * nb["Plat"])
    swamp_raw = blur(((zone_map == ZI["swamp"]) | (zone_map == ZI["mangrove_swamp"])).astype(np.float32), 10)

    # the great range
    U = mountain_uplift(rng, X, Z)
    U = U * smooth(Ld / 70.0)                                            # ranges taper before the coast
    cd = np.exp(-((X - PEAK_X) / 26.0) ** 2) * smooth((Z - PEAK_Z - 6) / 30.0)   # calm near face for the stream
    mult = 0.55 + 0.9 * Rg + 0.4 * (nb["Rf"] - 0.35)
    mult = mult * (1 - cd) + 0.88 * cd
    m = np.clip(U / 22.0, 0, 1)
    hint = hint * (1 - m) + 70.0 * m + U * mult

    # the stage meadow: gently rolling, 66..74, from the beach to the lake
    raw = 70.0 + 2.2 * nL + 1.2 * nM + 0.4 * nH
    hm = 70.0 + 3.4 * np.tanh((raw - 70.0) / 3.4)
    mm = np.maximum(smooth((46.0 - np.abs(X)) / 8.0), smooth((88.0 - np.abs(X + 10.0 * nL)) / 46.0))
    mm = mm * smooth((Z - (LAKE_CZ + LAKE_RZ - 20)) / 26.0)
    hint = hint * (1 - mm) + hm * mm

    # swamps overrule the range: flat wet ground at sea level with shallow pools (which fill with sea water)
    hint = np.maximum(hint, 62.6)
    sw = smooth((swamp_raw - 0.35) / 0.4)
    swamp_h = np.maximum(62.8 + 0.9 * nM + 0.3 * nH - 4.8 * smooth((nb["pool"] - 0.3) / 0.35), 58.5)
    hint = hint * (1 - sw) + swamp_h * sw

    # coast: a gentle sand beach rising from the sea, or a cliff on rocky coasts
    cliff = smooth(nb["cliff"] / 0.55) * np.clip(rm["cliff"], 0, 1)
    cliff = cliff * smooth((np.hypot(X, Z - S0_DESIGN) - 90) / 90.0)       # never on the stage beach
    Lp = np.clip(Ld, 0, 80)
    hb = 62.4 + 0.12 * Lp
    a = lerp(smooth((Lp - 5) / 38.0), smooth(Lp / 6.0), cliff)
    Hl = lerp(hb, hint, a)
    ds = np.clip(-Ld, 0, None)
    sc = 9.0 * (1 - 0.55 * cliff)
    Hs = SEA - 20.0 * (1 - np.exp(-(ds / sc) ** 1.4))
    return np.where(Ld > 0, Hl, Hs).astype(np.float32), cliff, rm, U * mult


# ------------------------------------------------------------------ 3. the stage features


def smooth1d(a, s):
    k = int(3 * s) + 1
    x = np.arange(-k, k + 1)
    g = np.exp(-x * x / (2.0 * s * s))
    return np.convolve(np.pad(np.asarray(a, float), (k, k), mode="edge"), g / g.sum(), "valid")


def shore_z(H):
    """z of the shoreline on the +z axis: the last land column going south at x = 0."""
    col = H[N]
    return int(np.flatnonzero(col >= SEA)[-1]) - N


def stage_features(rng, X, Z, Hf, nb):
    """The great mountain's summit, the stage lake, the stream down its near face, the clearing.
    Returns Hf and a dict with S0, CLEAR_Z, lake, stream, spring."""
    info = {}
    # --- the greatest mountain: nothing else may stand taller; its summit is a horn at (PEAK_X, PEAK_Z)
    r = np.hypot(X - PEAK_X, Z - PEAK_Z)
    others = float(Hf[r > 46].max())
    if others > 170:
        Hf = np.where(Hf > 148, 148 + (Hf - 148) * 22.0 / (others - 148), Hf)
    horn = PEAK_Y - 1.05 * r - 0.012 * r * r
    wgt = smooth((50.0 - r) / 32.0)
    Hf = np.where(wgt > 0, Hf * (1 - wgt) + np.maximum(horn, 66.0) * wgt, Hf)
    Hf = np.where(r < 0.6, PEAK_Y, Hf)

    # --- the stage lake: an ellipse of sea level water, bed 56..60, gently banked
    e = ((X - LAKE_CX) / LAKE_RX) ** 2 + ((Z - LAKE_CZ) / LAKE_RZ) ** 2 + 0.11 * nb["lake"]
    bed = 60.0 - 4.0 * smooth((1 - e) / 0.6)
    bank = np.maximum(62.3, np.minimum(Hf, 62.3 + 9.0 * (e - 1) + 6.0 * (e - 1) ** 2))
    Hf = np.where(e < 1, bed, np.where(Hf >= SEA, bank, Hf))
    lake_mask = e < 1
    info["lake_e"] = e

    # --- the clearing and the meadow (the meadow is clipped to 66..74 inside the stage rectangle)
    S0 = shore_z(np.rint(Hf))
    CLEAR_Z = S0 - 45
    info["S0"], info["CLEAR_Z"] = S0, CLEAR_Z
    rc = np.hypot(X, Z - CLEAR_Z)
    inrect = (np.abs(X) < 40) & (Z > LAKE_CZ + LAKE_RZ + 4) & (Z < S0 - 20)
    Hf = np.where(inrect, np.clip(Hf, 66.4, 73.6), Hf)
    c = smooth((CLEAR_R_OUT - rc) / (CLEAR_R_OUT - CLEAR_R_IN))
    Hf = np.where(rc <= CLEAR_R_IN, float(CLEAR_Y), Hf * (1 - c) + CLEAR_Y * c)

    # --- the stream: straight down the near face along x = 0, one block deep, falling at least 1 every 3 columns
    zl = next(z for z in range(30, 200) if Hf[N, z + N] < SEA)          # first lake column going south
    z_end = zl - 1
    prof = smooth1d(Hf[N - 3:N + 4, :].mean(axis=0), 3.0)
    G = {z_end: SEA + 1}                                                 # ground beside the channel
    top = None
    for z in range(z_end - 1, PEAK_Z + 4, -1):
        G[z] = max(G[z + 1] + (1 if (z_end - z) % 3 == 0 else 0), int(round(prof[z + N])))
        if G[z] >= 156:
            top = z
            break
    for z in range(top, z_end + 1):
        for x in range(-8, 9):
            if x == 0:
                Hf[N, z + N] = G[z] - 1
            else:
                s = smooth((abs(x) - 1) / 7.0)
                Hf[N + x, z + N] = G[z] * (1 - s) + Hf[N + x, z + N] * s
    info["stream"] = [(0, z) for z in range(top, z_end + 1)]
    info["spring"] = (0, G[top], top)
    info["lake_mask"] = lake_mask
    return Hf, info


# ------------------------------------------------------------------ 4. rivers and lakes


def flow_routing(Hc, sea):
    """Priority-flood on a coarse grid: fills hollows so every land cell drains to the sea.  Returns the receiver
    cell of each cell (-1 for sea) and the flow accumulation (number of cells draining through each cell)."""
    h, w = Hc.shape
    flat = Hc.ravel()
    seaf = sea.ravel()
    n = h * w
    recv = np.full(n, -1, dtype=np.int64)
    filled = flat.astype(np.float64).copy()
    seen = seaf.copy()
    heap = [(float(flat[i]), int(i)) for i in np.flatnonzero(seaf)]
    heapq.heapify(heap)
    nbrs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    while heap:
        e, i = heapq.heappop(heap)
        r, c = divmod(i, w)
        for dr, dc in nbrs:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                j = rr * w + cc
                if not seen[j]:
                    seen[j] = True
                    recv[j] = i
                    fe = max(float(flat[j]), e + 1e-3)
                    filled[j] = fe
                    heapq.heappush(heap, (fe, j))
    acc = np.ones(n, dtype=np.int64)
    for i in np.argsort(-filled):
        r = recv[i]
        if r >= 0 and not seaf[i]:
            acc[r] += acc[i]
    return recv, acc


def chaikin(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        out.append(pts[-1])
        pts = out
    return pts


def resample(pts, step=1.0):
    p = np.array(pts, dtype=float)
    seg = np.hypot(*(p[1:] - p[:-1]).T)
    s = np.concatenate(([0], np.cumsum(seg)))
    u = np.arange(0, s[-1], step)
    return np.stack([np.interp(u, s, p[:, 0]), np.interp(u, s, p[:, 1])], axis=1)


def river_profile(wd, locks):
    """Quantise the desired (non-increasing) water level into level reaches that drop one block at a time.
    A reach is at least 3 columns long (2, or 1 where the ground is steep and the river must keep up);
    inside a lock (an elevated lake) the level does not change."""
    w = np.zeros(len(wd), dtype=np.int64)
    cur = max(int(math.floor(wd[0])), SEA)
    last = -99
    for i in range(len(wd)):
        if not any(a <= i <= b for a, b in locks):
            tgt = min(math.floor(wd[i]), SEA + (len(wd) - 1 - i) // 2)     # and be at sea level by the mouth
            lag = cur - tgt
            if lag >= 1 and cur > SEA:
                need = 3 if lag < 2 else (2 if lag < 4 else 1)
                if i - last >= need:
                    cur -= 1
                    last = i
        w[i] = cur
    return w


def plan_rivers(rng, X, Z, Hf, info, nb, want=10):
    """Choose river paths by routing the terrain's drainage; returns a list of dicts with the unit-spaced
    path, desired level, widths and the elevated lakes on it."""
    step = 3
    Hs = blur(Hf, 2.5)
    Hc = Hs[::step, ::step]
    sea = Hc < SEA + 0.3
    recv, acc = flow_routing(Hc, sea)
    h, w = Hc.shape
    seaf = sea.ravel()
    kids = [[] for _ in range(h * w)]
    for i in range(h * w):
        if recv[i] >= 0:
            kids[recv[i]].append(i)
    xy = lambda i: (step * (i // w) - N, step * (i % w) - N)
    protected = lambda x, z: abs(x) < 72 and z > 30
    hflat = Hc.ravel()
    cand = [i for i in range(h * w) if not seaf[i] and 78 <= hflat[i] <= 132 and acc[i] >= 7]
    cand = [i for i in cand if acc[i] >= 10]
    cand.sort(key=lambda i: -(min(hflat[i], 126) + 0.02 * min(acc[i], 200)))      # high valley heads first
    used, sources, rivers = set(), [], []
    for i in cand:
        x, z = xy(i)
        if protected(x, z) or math.hypot(x - PEAK_X, z - PEAK_Z) < 75:
            continue
        if any(math.hypot(x - a, z - b) < 40 for a, b in sources):
            continue
        path, cur, bad = [i], i, False
        while recv[cur] >= 0 and not seaf[cur]:
            cur = recv[cur]
            if cur in used:
                bad = True
                break
            path.append(cur)
        pts = [xy(j) for j in path]
        length = sum(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(pts, pts[1:]))
        if bad or length < 85 or any(protected(px, pz) for px, pz in pts):
            continue
        for j in path:
            r0, c0 = divmod(j, w)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    used.add((r0 + dr) * w + c0 + dc)
        sources.append((x, z))
        rivers.append(pts)
        if len(rivers) >= want:
            break
    return rivers

def carve_lake(Hf, water, lake_mask, X, Z, nb, cx, cz, r, ang, wl):
    """An elevated lake: a bowl of level water (surface y = wl) on a plateau a little above the surface, which
    blends back into the ground around it, so the banks stand at least a block above the water all round."""
    a, b = 1.2 * r, 0.85 * r
    R = int(2.2 * max(a, b) + 24)
    x0, x1 = max(int(cx) - R + N, 0), min(int(cx) + R + N + 1, W)
    z0, z1 = max(int(cz) - R + N, 0), min(int(cz) + R + N + 1, W)
    sx, sz = X[x0:x1, z0:z1], Z[x0:x1, z0:z1]
    u = (sx - cx) * math.cos(ang) + (sz - cz) * math.sin(ang)
    v = -(sx - cx) * math.sin(ang) + (sz - cz) * math.cos(ang)
    e = (u / a) ** 2 + (v / b) ** 2 + 0.25 * nb["lake"][x0:x1, z0:z1]
    ds = (np.sqrt(np.maximum(e, 0)) - 1.0) * 0.5 * (a + b)
    tgt = wl + 1.6 + 0.35 * nb["H"][x0:x1, z0:z1]
    wf = 1 - smooth((ds - 4.0) / 15.0)
    sub = Hf[x0:x1, z0:z1]
    newh = np.where(ds > 0, sub * (1 - wf) + tgt * wf, sub)
    newh = np.where(ds > 0, np.maximum(newh, np.where(ds < 4.5, wl + 1.0, 0)), newh)
    inside = e < 1
    depth = 3.0 * smooth((1 - e) / 0.7)
    newh = np.where(inside, wl - 1.0 - depth, newh)
    Hf[x0:x1, z0:z1] = newh
    water[x0:x1, z0:z1] = np.where(inside, wl, water[x0:x1, z0:z1])
    lake_mask[x0:x1, z0:z1] |= inside
    return int(inside.sum())


def build_tarns(rng, X, Z, Hf, water, lake_mask, nb, Ueff, Ld, lakes, rivers, count=3):
    """Mountain lakes that are not on a river: small level lakes in hollows of the high ground, at several heights."""
    gx, gz = np.gradient(blur(Hf, 4.0))
    flat = blur(np.hypot(gx, gz), 7.0)
    occupied = (water >= 0) | lake_mask
    near = edt(occupied, 60) < 55
    out = []
    bands = [(96, 110), (114, 128), (132, 148)][:count]
    for lo, hi in bands:
        Hs = blur(Hf, 3.0)
        ok = (Ueff > 18) & (Hs > lo) & (Hs < hi) & (flat < 1.6) & ~near & (Ld > 40)
        ok &= ~((np.abs(X) < 75) & (Z > -80))                         # not on the stage face
        ok &= np.hypot(X - PEAK_X, Z - PEAK_Z) > 55
        score = np.where(ok, 0.5 * rng.random(Hf.shape) - flat, -9.0)
        i, j = np.unravel_index(int(np.argmax(score)), score.shape)
        if score[i, j] < -5:
            continue
        cx, cz = float(X[i, j]), float(Z[i, j])
        r = int(rng.integers(8, 12))
        wl = int(round(Hs[i, j] - 2))
        carve_lake(Hf, water, lake_mask, X, Z, nb, cx, cz, r, float(rng.random() * 3.14), wl)
        out.append({"cx": cx, "cz": cz, "r": r, "w": wl, "river": -1})
        occupied = (water >= 0) | lake_mask
        near = edt(occupied, 60) < 55
    return out


def build_rivers(rng, X, Z, Hf, info, nb, want=10):
    """Make the rivers and their elevated lakes.  Returns Hf, water (int16, -1 none), river_mask, river list, lake list."""
    Hs = blur(Hf, 2.0)
    raw = plan_rivers(rng, X, Z, Hf, info, nb, want)
    water = np.full(Hf.shape, -1, dtype=np.int16)
    rmask = np.zeros(Hf.shape, dtype=bool)
    lake_mask = np.zeros(Hf.shape, dtype=bool)
    xi = np.arange(-N, N + 1, dtype=np.float32)
    rivers, lakes = [], []
    all_lakes_xy = []
    for pts in raw:
        pts = chaikin(pts, 3)
        p = resample(pts, 1.0)
        M = len(p)
        if M < 70:
            continue
        # meander: more where the ground is flat; tapered at both ends
        tan = np.gradient(p, axis=0)
        tan /= np.maximum(np.hypot(tan[:, 0], tan[:, 1]), 1e-6)[:, None]
        nor = np.stack([-tan[:, 1], tan[:, 0]], axis=1)
        T0 = sample(Hs, p[:, 0], p[:, 1])
        sl = np.abs(np.gradient(smooth1d(T0, 6.0))) * 1.0
        amp = 7.0 * (1 - smooth(smooth1d(sl, 8.0) / 0.35))
        s = np.arange(M)
        ph = rng.random(3) * 6.28
        off = amp * (0.6 * np.sin(2 * np.pi * s / 95.0 + ph[0]) + 0.4 * np.sin(2 * np.pi * s / 43.0 + ph[1]))
        off = off * smooth(s / 25.0) * smooth((M - 1 - s) / 25.0)
        p = p + nor * off[:, None]
        p[:, 0] = np.clip(p[:, 0], -N + 2, N - 2)
        p[:, 1] = np.clip(p[:, 1], -N + 2, N - 2)
        p = resample(chaikin([tuple(q) for q in p[::4]], 2), 1.0)
        M = len(p)
        Tp = smooth1d(sample(Hs, p[:, 0], p[:, 1]), 5.0)
        # trim the part of the path that is already out at sea
        inland = np.flatnonzero(Tp > SEA + 0.5)
        if len(inland) < 55:
            continue
        p, Tp = p[:inland[-1] + 4], Tp[:inland[-1] + 4]
        M = len(p)
        s = np.arange(M)
        tan = np.gradient(p, axis=0)
        tan /= np.maximum(np.hypot(tan[:, 0], tan[:, 1]), 1e-6)[:, None]
        wd = np.minimum.accumulate(Tp - 2.0)
        # elevated lakes on flat stretches
        slope = np.abs(Tp[28:] - Tp[:-28]) / 28.0
        locks, lks = [], []
        for part in (0, 1):
            lo, hi = (45, M // 2) if part == 0 else (M // 2 + 10, M - 70)
            best, bs = None, 1e9
            for i in range(lo, min(hi, M - 70), 5):
                if i - 14 < 0 or i + 14 >= len(slope) + 14:
                    continue
                if not (68 <= Tp[i] <= 140):
                    continue
                if any(math.hypot(p[i, 0] - a, p[i, 1] - b) < 90 for a, b in all_lakes_xy):
                    continue
                if abs(p[i, 0]) < 90 and p[i, 1] > 0:
                    continue
                sc = slope[i - 14] + 0.002 * abs(i - (lo + hi) / 2)
                if sc < bs:
                    bs, best = sc, i
            if best is not None and bs < 0.2:
                r = int(rng.integers(10, 17))
                locks.append((best - r, best + r))
                lks.append((best, r))
                all_lakes_xy.append((p[best, 0], p[best, 1]))
        wq = river_profile(wd, locks)
        hw = 1.15 + 0.7 * smooth(s / 90.0) + 1.5 * smooth((s - 0.45 * M) / (0.55 * M))
        rivers.append({"p": p, "w": wq, "hw": hw, "locks": locks, "Tp": Tp})
        for (ic, r) in lks:
            ang = math.atan2(tan[ic, 1], tan[ic, 0])
            lakes.append({"cx": float(p[ic, 0]), "cz": float(p[ic, 1]), "r": r, "ang": ang, "w": int(wq[max(ic - r, 0)]), "river": len(rivers) - 1})
    # ---- elevated lakes first (bowl + level plateau), then the river valleys cut through
    for lk in lakes:
        lk["area"] = carve_lake(Hf, water, lake_mask, X, Z, nb, lk["cx"], lk["cz"], lk["r"], lk["ang"], lk["w"])
    # ---- river valleys
    pxs, pzs, pws, phs, pseas = [], [], [], [], []
    for ri, rv in enumerate(rivers):
        for k in range(len(rv["p"])):
            if any(a <= k <= b for a, b in rv["locks"]):
                continue
            pxs.append(rv["p"][k, 0]); pzs.append(rv["p"][k, 1]); pws.append(rv["w"][k])
            phs.append(rv["hw"][k] * (1.25 if rv["w"][k] <= SEA else 1.0)); pseas.append(rv["w"][k] <= SEA)
    pxs, pzs = np.array(pxs), np.array(pzs)
    pws, phs, pseas = np.array(pws), np.array(phs), np.array(pseas)
    best = np.full(Hf.shape, 1e9, dtype=np.float32)
    owner = np.full(Hf.shape, -1, dtype=np.int32)
    for k in range(len(pxs)):
        Wk = int(phs[k] + 26)
        ix, iz = int(round(pxs[k])) + N, int(round(pzs[k])) + N
        x0, x1, z0, z1 = max(ix - Wk, 0), min(ix + Wk + 1, W), max(iz - Wk, 0), min(iz + Wk + 1, W)
        d2 = (xi[x0:x1, None] - pxs[k]) ** 2 + (xi[None, z0:z1] - pzs[k]) ** 2
        sub = best[x0:x1, z0:z1]
        m = d2 < sub
        sub[m] = d2[m]
        owner[x0:x1, z0:z1][m] = k
    has = (owner >= 0) & ~lake_mask
    o = np.where(has, owner, 0)
    dist = np.sqrt(best)
    w_o, hw_o, sea_o = pws[o], phs[o], pseas[o]
    wob = 0.45 * nb["H"]
    isw = has & (dist <= hw_o + wob)
    centre = dist < hw_o - 1.2
    w_eff = np.maximum(w_o, SEA)
    bedh = np.where(sea_o, 60.0 - centre, w_o - 1.0 - centre)
    wall = w_eff + 1.0 + 0.62 * (dist - hw_o)
    f = 1 - smooth((dist - hw_o - 6.0) / 18.0)
    Hn = Hf - f * np.maximum(Hf - wall, 0)
    Hn = np.where(dist <= hw_o + 2.0, np.maximum(Hn, w_eff + 1.0), Hn)
    Hn = np.where(isw, bedh, Hn)
    Hf = np.where(has, Hn, Hf).astype(np.float32)
    water = np.where(isw & (w_o > SEA), w_o, water).astype(np.int16)
    rmask = isw
    return Hf, water, rmask, lake_mask, rivers, lakes


def repair_levels(H, water):
    """Adjacent inland water columns (and sea water beside them) may differ by at most one block of level.  Where the
    river stamping left a bigger step (steep rapids), take the 1-Lipschitz lower envelope of the levels: a
    multi-source Dijkstra over the water columns, lowest first.  Beds are cut down to stay under the new surface."""
    w = water.astype(np.int32)
    ww = w >= 0
    near = np.zeros(w.shape, dtype=bool)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            near |= np.roll(np.roll(ww, dx, 0), dz, 1)
    sea_adj = near & (H < SEA) & ~ww
    best = {}
    heap = []
    for i, j in np.argwhere(ww):
        best[(int(i), int(j))] = int(w[i, j])
        heap.append((int(w[i, j]), int(i), int(j)))
    for i, j in np.argwhere(sea_adj):
        best[(int(i), int(j))] = SEA
        heap.append((SEA, int(i), int(j)))
    heapq.heapify(heap)
    while heap:
        lv, i, j = heapq.heappop(heap)
        if lv > best[(i, j)]:
            continue
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                n = (i + dx, j + dz)
                if (dx or dz) and n in best and best[n] > lv + 1:
                    best[n] = lv + 1
                    heapq.heappush(heap, (lv + 1, n[0], n[1]))
    H = H.copy()
    for (i, j), lv in best.items():
        if ww[i, j] and lv < w[i, j]:
            w[i, j] = lv
            H[i, j] = min(H[i, j], lv - 1)
    return H, w.astype(np.int16)


def fix_banks(H, water):
    """Every inland water column above sea level needs ground at least one block above its surface on all sides
    (apart from other water of the same body and the next reach down).  Raise banks where they fall short."""
    for _ in range(3):
        wl = np.where(water >= 0, water.astype(np.int32), -1)
        wmax = wl.copy()
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx or dz:
                    sh = np.full(wl.shape, -1, dtype=np.int32)
                    sx = slice(max(dx, 0), wl.shape[0] + min(dx, 0))
                    tx = slice(max(-dx, 0), wl.shape[0] + min(-dx, 0))
                    sz = slice(max(dz, 0), wl.shape[1] + min(dz, 0))
                    tz = slice(max(-dz, 0), wl.shape[1] + min(-dz, 0))
                    sh[tx, tz] = wl[sx, sz]
                    wmax = np.maximum(wmax, sh)
        need = np.where((water < 0) & (wmax >= 0), wmax + 1, 0)
        H = np.maximum(H, need).astype(H.dtype)
    return H


# ------------------------------------------------------------------ 5. zones

PEAK_SEEDS = [("frozen_peaks", 0, -30, 0.9), ("frozen_peaks", 98, -79, 0.8),
              ("jagged_peaks", 5, -100, 1.3), ("jagged_peaks", -10, -210, 1.3),
              ("stony_peaks", -79, -72, 1.0), ("stony_peaks", -137, -124, 1.0)]
PEAK_T, SLOPE_T, GROVE_T = 129, 114, 96          # height bands of the great range
BASE_COLD = {"snowy_taiga", "snowy_plains", "ice_spikes"}
HOT = ["desert", "badlands", "wooded_badlands", "eroded_badlands", "savanna", "savanna_plateau", "windswept_savanna",
       "jungle", "sparse_jungle", "bamboo_jungle", "swamp", "mangrove_swamp", "mushroom_fields"]
NO_BEACH = {"swamp", "mangrove_swamp", "mushroom_fields"}
ROCKY = {"windswept_hills", "windswept_forest", "windswept_gravelly_hills", "windswept_savanna", "badlands",
         "eroded_badlands", "wooded_badlands", "savanna_plateau"}


def finish_zones(rng, X, Z, H, water, zone0, rmask, Ld, cliff, Ueff, info, nb):
    """Zones from the climate layout, corrected by what the terrain actually did."""
    zone = zone0.astype(np.uint8).copy()
    base = zone0.copy()
    land = Ld > 0
    isin = lambda zs: np.isin(base, [ZI[z] for z in zs])

    # the great range by height band; the peaks are split into three kinds by region
    mtn = (Ueff > 12) & land
    pidx = voronoi(PEAK_SEEDS, X, Z, rng, warp=10.0, jitter=6.0)
    pz = np.array([ZI[s[0]] for s in PEAK_SEEDS], dtype=np.uint8)[pidx]
    hot = isin(HOT)
    notwind = ~isin(["windswept_hills", "windswept_forest", "windswept_gravelly_hills"]) & ~hot   # hot ground keeps its zone
    zone = np.where(mtn & notwind & (H >= GROVE_T), ZI["grove"], zone)
    zone = np.where(mtn & notwind & (H >= SLOPE_T), ZI["snowy_slopes"], zone)
    pz = np.where(hot, ZI["stony_peaks"], pz)
    zone = np.where(mtn & (H >= PEAK_T), pz, zone)
    zone = zone.astype(np.uint8)

    # swamps are low and flat: where the ground rose, the land is jungle instead
    zone = np.where(((zone == ZI["swamp"]) | (zone == ZI["mangrove_swamp"])) & (H > 67), ZI["sparse_jungle"], zone).astype(np.uint8)

    # the stage meadow is plains
    zone = np.where((np.abs(X) < 35) & (Z >= LAKE_CZ + LAKE_RZ + 3) & (Z <= info["S0"] - 12), ZI["plains"], zone).astype(np.uint8)

    # shores
    band = land & (Ld <= 7.0)
    cold = isin(BASE_COLD)
    rocky = isin(ROCKY)
    nobeach = isin(NO_BEACH)
    zone = np.where(band & ~nobeach & (H <= 66), np.where(cold, ZI["snowy_beach"], ZI["beach"]), zone)
    zone = np.where(band & ~nobeach & ((cliff > 0.45) | (rocky & (H > 66))) & (H > 63), ZI["stony_shore"], zone)
    zone = zone.astype(np.uint8)

    # islets keep their own zone; the strange one is the mushroom island
    lab, sizes = components(land)
    if info.get("mushroom") is not None:
        cx, cz = info["mushroom"]
        k = lab[cx + N, cz + N]
        if k > 0:
            zone = np.where(lab == k, ZI["mushroom_fields"], zone).astype(np.uint8)

    # the sea by climate; inland hollows keep the land zone
    sea = (H < SEA) & (Ld < 0.5)
    sidx = voronoi(SEA_SEEDS, X, Z, rng, warp=40.0, jitter=14.0)
    sz = np.array([ZI[s[0]] for s in SEA_SEEDS], dtype=np.uint8)[sidx]
    zone = np.where(sea, sz, zone).astype(np.uint8)

    # rivers: frozen in the cold north
    zone = np.where(rmask, np.where(cold, ZI["frozen_river"], ZI["river"]), zone).astype(np.uint8)
    return repair_zones(zone, X, Z, info)


GROWABLE = ["plains", "sunflower_plains", "meadow", "forest", "flower_forest", "birch_forest", "old_growth_birch_forest",
            "dark_forest", "dappled_forest", "pale_garden", "cherry_grove", "taiga", "old_growth_pine_taiga",
            "old_growth_spruce_taiga", "snowy_taiga", "snowy_plains", "windswept_hills", "windswept_forest",
            "windswept_gravelly_hills", "savanna", "savanna_plateau", "windswept_savanna", "desert", "badlands",
            "wooded_badlands", "eroded_badlands", "jungle", "sparse_jungle", "bamboo_jungle"]


def dilate4(m):
    o = m.copy()
    o[1:] |= m[:-1]
    o[:-1] |= m[1:]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    return o


POOLS = [GROWABLE, ["frozen_peaks", "jagged_peaks", "stony_peaks", "snowy_slopes"], ["swamp", "mangrove_swamp"]]


def repair_zones(zone, X, Z, info):
    """Safety net: a river or a shore may cut a zone into pieces.  Any land zone whose biggest piece is under the
    minimum is grown, ring by ring, into neighbouring big zones of the same kind (ordinary land, high ground or
    wetland) until it has room to spare."""
    need = MIN_AREA + 250
    protect = (np.abs(X) < 48) & (Z > LAKE_CZ - 10)                       # the stage stays as laid out
    for pool in POOLS:
        for name in pool:
            if name == "snowy_slopes":
                continue
            zi = ZI[name]
            lab, sizes = components(zone == zi)
            big = int(sizes[1:].max()) if len(sizes) > 1 else 0
            if big >= need or big == 0:
                continue
            lz, nz_, vz = label(zone)
            pz = np.bincount(lz.ravel(), minlength=nz_)
            donor_labels = [k for k in range(nz_) if pz[k] >= 2600 and ZONES[int(vz[k])] in pool and int(vz[k]) != zi]
            donors = np.isin(lz, donor_labels) & ~protect
            k = 1 + int(np.argmax(sizes[1:]))
            patch = lab == k
            for _ in range(90):
                if patch.sum() >= need:
                    break
                ring = dilate4(patch) & donors & ~patch
                if not ring.any():
                    break
                patch = patch | ring
            zone = np.where(patch & (donors | (zone == zi)), zi, zone).astype(np.uint8)
    return zone


# ------------------------------------------------------------------ 4b. inland lakes at sea level


def build_sea_lakes(rng, X, Z, Hf, water, nb, Ueff, Ld, lake_mask, count=3):
    """A few lakes at sea level (bed 56..60) on flat inland ground; the sea's water is simply left in them when
    the land rises.  Returns Hf, list of dicts."""
    gx, gz = np.gradient(blur(Hf, 3.0))
    flat = blur(np.hypot(gx, gz), 6.0)
    wat = (water >= 0) | lake_mask | (Hf < SEA + 2)
    far = edt(wat, 60) > 24
    ok = far & (Ld > 35) & (Ueff < 8) & (Hf > 65) & (Hf < 90) & (flat < 0.5)
    ok &= ~((np.abs(X) < 90) & (Z > 20))                      # leave the stage alone
    lakes = []
    for k in range(count):
        score = np.where(ok, rng.random(Hf.shape), -1.0)
        for lk in lakes:
            score = np.where(np.hypot(X - lk["cx"], Z - lk["cz"]) < 90, -1.0, score)
        i, j = np.unravel_index(int(np.argmax(score)), score.shape)
        if score[i, j] < 0:
            break
        cx, cz = float(X[i, j]), float(Z[i, j])
        rx, rz = float(rng.integers(13, 21)), float(rng.integers(9, 15))
        ang = float(rng.random() * math.pi)
        u = (X - cx) * math.cos(ang) + (Z - cz) * math.sin(ang)
        v = -(X - cx) * math.sin(ang) + (Z - cz) * math.cos(ang)
        e = (u / rx) ** 2 + (v / rz) ** 2 + 0.2 * nb["lake"]
        win = e < 4
        bed = 60.0 - 4.0 * smooth((1 - e) / 0.6)
        bank = np.maximum(62.3, np.minimum(Hf, 62.3 + 7.0 * (e - 1) + 4.0 * (e - 1) ** 2))
        Hf = np.where(win, np.where(e < 1, bed, bank), Hf).astype(np.float32)
        lakes.append({"cx": cx, "cz": cz, "rx": rx, "rz": rz, "level": SEA})
        ok &= np.hypot(X - cx, Z - cz) > 50
    return Hf, lakes


# ------------------------------------------------------------------ 6. caves


def rects2d(layer):
    """Greedy decomposition of a boolean [x, z] layer into rectangles (x1, x2, z1, z2): z-runs merged along x."""
    out, openr = [], {}
    nx = layer.shape[0]
    for x in range(nx + 1):
        cur = set()
        if x < nx:
            row = np.concatenate(([False], layer[x], [False]))
            d = np.flatnonzero(row[1:] != row[:-1])
            cur = {(int(a), int(b) - 1) for a, b in zip(d[::2], d[1::2])}
        for key in list(openr):
            if key not in cur:
                out.append((openr.pop(key), x - 1, key[0], key[1]))
        for key in cur:
            openr.setdefault(key, x)
    return out


def merge_boxes(vox, ox, oy, oz):
    """Greedy box decomposition of a dense boolean [x, y, z] array -> inclusive (x1, y1, z1, x2, y2, z2) boxes."""
    ny = vox.shape[1]
    boxes, openb = [], {}
    for y in range(ny + 1):
        cur = set(rects2d(vox[:, y, :])) if y < ny else set()
        for key in list(openb):
            if key not in cur:
                y0 = openb.pop(key)
                boxes.append((key[0] + ox, y0 + oy, key[2] + oz, key[1] + ox, y - 1 + oy, key[3] + oz))
        for key in cur:
            openb.setdefault(key, y)
    return boxes


_BALLS = {}


def ball(r):
    k = int(round(r * 2))
    if k not in _BALLS:
        rr = k / 2.0
        n = int(math.ceil(rr))
        a = np.arange(-n, n + 1)
        _BALLS[k] = (a[:, None, None] ** 2 + a[None, :, None] ** 2 + a[None, None, :] ** 2) <= rr * rr + 0.3
    return _BALLS[k]


def minfilter(a, r):
    out = a.copy()
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            sh = np.roll(np.roll(a, dx, 0), dz, 1)
            out = np.minimum(out, sh)
    return out


def build_caves(rng, X, Z, H, water, stream, info, Ld, want=32):
    """Worm tunnels that start on hillsides and dive into the rock, some ending in a cavern.  Caves keep out of
    a margin round all water, round the clearing and the stage corridor, and stay 3+ blocks under the surface
    (except at their mouths).  Returns (boxes, entrances)."""
    wcol = (H < SEA) | (water >= 0)
    for (x, z) in stream:
        wcol[x + N, z + N] = True
    nearw = edt(wcol, 12) < 8.5
    forbid = nearw | (np.hypot(X, Z - info["CLEAR_Z"]) < 46) | ((np.abs(X) < 22) & (Z > PEAK_Z - 8)) | (Ld < 12)
    Hs = blur(H.astype(np.float32), 2.5)
    gx, gz = np.gradient(Hs)
    slope = np.hypot(gx, gz)
    Hmin = minfilter(H.astype(np.int16), 3)
    cand = np.argwhere((H >= 76) & ~forbid & (slope > 0.45) & (slope < 1.8))
    order = rng.permutation(len(cand))
    entr = []
    for k in order:
        i, j = cand[k]
        if all((i - a) ** 2 + (j - b) ** 2 > 30 * 30 for a, b in entr):
            entr.append((int(i), int(j)))
            if len(entr) >= want * 2:
                break
    boxes, entrances = [], []
    systems = 0
    for (i, j) in entr:
        if systems >= want:
            break
        x, z = i - N, j - N
        up = np.array([gx[i, j], gz[i, j]])
        up = up / max(np.hypot(*up), 1e-6)
        paths = []
        cavern = None
        head = np.array([up[0], -0.18, up[1]])
        pos = np.array([float(x), H[i, j] - 1.0, float(z)])
        main = []
        steps = int(rng.integers(70, 150))
        base_r = float(rng.choice([2.0, 2.5, 3.0]))
        ph = rng.random(4) * 6.28
        for s in range(steps):
            head = head + rng.normal(0, 0.11, 3) * np.array([1.0, 0.45, 1.0])
            head[1] = np.clip(head[1], -0.32, 0.18)
            head = head / np.linalg.norm(head)
            pos = pos + head * 1.7
            xi, zi = int(round(pos[0])) + N, int(round(pos[2])) + N
            if not (3 <= xi < W - 3 and 3 <= zi < W - 3) or forbid[xi, zi]:
                break
            rad = base_r * (0.82 + 0.3 * math.sin(s * 0.23 + ph[0]) * math.sin(s * 0.11 + ph[1]))
            if s > 6 and pos[1] + rad > Hmin[xi, zi] - 3.0:
                pos[1] = Hmin[xi, zi] - 3.0 - rad
                head[1] = min(head[1], -0.1)
            if pos[1] - rad < FLOOR + 4:
                break
            main.append((pos.copy(), rad))
            if s == steps // 2 and rng.random() < 0.5:                 # a side tunnel
                paths.append(("side", pos.copy(), head.copy()))
        if len(main) < 30:
            continue
        paths.insert(0, ("main", None, None))
        lists = [main]
        for kind, p0, h0 in paths[1:]:
            h1 = np.array([-h0[2], h0[1], h0[0]]) * (1 if rng.random() < 0.5 else -1)
            pp, side = p0.copy(), []
            for s in range(int(rng.integers(30, 60))):
                h1 = h1 + rng.normal(0, 0.12, 3) * np.array([1.0, 0.45, 1.0])
                h1[1] = np.clip(h1[1], -0.3, 0.2)
                h1 = h1 / np.linalg.norm(h1)
                pp = pp + h1 * 1.7
                xi, zi = int(round(pp[0])) + N, int(round(pp[2])) + N
                if not (3 <= xi < W - 3 and 3 <= zi < W - 3) or forbid[xi, zi]:
                    break
                if pp[1] + base_r > Hmin[xi, zi] - 3.0:
                    pp[1] = Hmin[xi, zi] - 3.0 - base_r
                if pp[1] - base_r < FLOOR + 4:
                    break
                side.append((pp.copy(), base_r * 0.9))
            if len(side) > 8:
                lists.append(side)
        # a cavern at the end of the main tunnel (not every time)
        end = main[-1][0]
        ends = [(end, 1)]
        if len(lists) > 1:
            ends.append((lists[-1][-1][0], 1))
        caverns = []
        for e0, _ in ends:
            if rng.random() < 0.7:
                ry = float(rng.uniform(4.5, 7.5))
                rxz = float(rng.uniform(8, 14))
                xi, zi = int(round(e0[0])) + N, int(round(e0[2])) + N
                cy = min(e0[1], Hmin[xi, zi] - 5 - ry)
                if cy - ry >= FLOOR + 4 and not forbid[max(xi - 14, 0):xi + 15, max(zi - 14, 0):zi + 15].any():
                    caverns.append((e0[0], cy, e0[2], rxz, ry, rxz * float(rng.uniform(0.7, 1.2))))
        allc = [c for lst in lists for c in lst]
        xs = [c[0][0] for c in allc]
        zs = [c[0][2] for c in allc]
        ys = [c[0][1] for c in allc]
        pad = 18
        ox, oz, oy = int(min(xs)) - pad, int(min(zs)) - pad, int(min(ys)) - 12
        nx, nz, ny = int(max(xs)) - ox + pad + 1, int(max(zs)) - oz + pad + 1, int(max(ys)) - oy + 14
        vox = np.zeros((nx, ny, nz), dtype=bool)
        for (cp, rad) in allc:
            b = ball(rad)
            n = b.shape[0] // 2
            cx_, cy_, cz_ = int(round(cp[0])) - ox, int(round(cp[1])) - oy, int(round(cp[2])) - oz
            vox[cx_ - n:cx_ + n + 1, cy_ - n:cy_ + n + 1, cz_ - n:cz_ + n + 1] |= b
        for (cxv, cyv, czv, rx, ry, rz) in caverns:
            wob = fnoise_small(rng, (int(2 * rx + 8), int(2 * ry + 8), int(2 * rz + 8)))
            gxs = np.arange(int(2 * rx + 8)) - (rx + 4)
            gys = np.arange(int(2 * ry + 8)) - (ry + 4)
            gzs = np.arange(int(2 * rz + 8)) - (rz + 4)
            sy = np.where(gys < 0, 0.62, 1.0)[None, :, None]
            d = (gxs[:, None, None] / rx) ** 2 + (gys[None, :, None] / (ry * sy)) ** 2 + (gzs[None, None, :] / rz) ** 2
            m = d < 1.0 + 0.45 * wob
            x0v, y0v, z0v = int(round(cxv - (rx + 4))) - ox, int(round(cyv - (ry + 4))) - oy, int(round(czv - (rz + 4))) - oz
            sl = (slice(max(x0v, 0), x0v + m.shape[0]), slice(max(y0v, 0), y0v + m.shape[1]), slice(max(z0v, 0), z0v + m.shape[2]))
            mm_ = m[max(-x0v, 0):, max(-y0v, 0):, max(-z0v, 0):]
            tgt = vox[sl]
            tgt |= mm_[:tgt.shape[0], :tgt.shape[1], :tgt.shape[2]]
        # filters: keep out of forbidden columns, stay under the surface (except at the mouth), above the floor margin
        gxi = np.arange(nx)[:, None] + ox + N
        gzi = np.arange(nz)[None, :] + oz + N
        inb = (gxi >= 0) & (gxi < W) & (gzi >= 0) & (gzi < W)
        gxc, gzc = np.clip(gxi, 0, W - 1), np.clip(gzi, 0, W - 1)
        colH = np.where(inb, H[gxc, gzc], 0)
        colF = forbid[gxc, gzc] | ~inb
        yy = np.arange(ny)[None, :, None] + oy
        mouth = (np.hypot(gxi - (x + N), gzi - (z + N)) < 7.0)[:, None, :]
        keep = ~colF[:, None, :] & (yy >= FLOOR + 4) & ((yy <= colH[:, None, :] - 3) | (mouth & (yy <= colH[:, None, :] + 3)))
        vox &= keep
        if vox.sum() < 200:
            continue
        # the mouth: the highest cave voxel within the mouth zone (an air block at the opening on the hillside)
        mv = np.argwhere(vox & mouth)
        if len(mv) == 0:
            continue
        top = mv[np.argmax(mv[:, 1])]
        boxes.extend(merge_boxes(vox, ox, oy, oz))
        entrances.append((int(top[0]) + ox, int(top[1]) + oy, int(top[2]) + oz))
        systems += 1
    return boxes, entrances


def fnoise_small(rng, shape):
    """Smooth 3D noise of unit-ish std for cavern walls (trilinear upsample of a coarse lattice)."""
    g = rng.standard_normal(tuple(s // 5 + 3 for s in shape)).astype(np.float32)
    out = g
    for ax, s in enumerate(shape):
        n = g.shape[ax]
        t = np.linspace(0, n - 1.001, s)
        i = t.astype(int)
        f = (t - i).reshape([-1 if a == ax else 1 for a in range(3)])
        out = np.take(out, i, axis=ax) * (1 - f) + np.take(out, i + 1, axis=ax) * f
    return out


# ------------------------------------------------------------------ 7. places


def anchor(mask):
    """The most interior column of the largest patch of a boolean mask (None if empty)."""
    lab, sizes = components(mask)
    if len(sizes) < 2:
        return None
    k = 1 + int(np.argmax(sizes[1:]))
    m = lab == k
    b = np.where(m, blur(m.astype(np.float32), 9.0), -1.0)
    i, j = np.unravel_index(int(np.argmax(b)), b.shape)
    return int(i) - N, int(j) - N


# (name, zone it stands in, how it looks to someone with no words for such things)
PLACE_ZONES = [
    ("the white spires", "ice_spikes", "Tall thin towers of white ice rise out of a flat white plain like the teeth of some great animal."),
    ("the red stone country", "badlands", "Flat-topped hills of red and orange and yellow stone, striped in layers, with almost nothing growing on them."),
    ("the sea of sand", "desert", "A wide land of pale sand without a single stream, heaped by the wind into long soft ridges."),
    ("the tall dry grass", "savanna", "Open ground of yellow grass as high as a knee, with a few flat-topped trees standing far apart."),
    ("the warm marsh", "swamp", "Low wet ground and still brown water, with heavy dark trees hung with trailing vines."),
    ("the roots that walk in water", "mangrove_swamp", "Trees standing on high tangled roots in shallow muddy water close to the sea."),
    ("the green tangle", "jungle", "A hot, steaming forest of huge trees wound about with creepers, so thick that the ground is always in shade."),
    ("the singing canes", "bamboo_jungle", "Straight green stalks as thick as a wrist and taller than any tree, creaking softly as they lean together."),
    ("the pink grove", "cherry_grove", "Gentle hills covered in trees whose leaves are pink, and petals drift down like snow."),
    ("the dark wood", "dark_forest", "A crowded forest of huge dark trees whose tops close out the sky, so that it is dim even at noon."),
    ("the pale wood", "pale_garden", "A quiet grey-white forest where the trees look bleached and the air is still and strange."),
    ("the field of gold", "sunflower_plains", "A wide plain full of tall yellow flowers that all turn their faces toward the sun."),
    ("the old giants", "old_growth_pine_taiga", "Enormous dark evergreen trees as old as the hills, with moss and ferns beneath them."),
    ("the island of strange caps", "mushroom_fields", "A small island far from shore where huge soft caps, red and brown, grow instead of trees."),
    ("the grey heights", "windswept_gravelly_hills", "Bare grey hills of loose stones where the wind blows hard and little grows."),
    ("the snow roof", "frozen_peaks", "The highest white ground, ice and snow all around, where the air is thin and bitterly cold."),
    ("the singing shore", "stony_shore", "A coast of grey boulders and cliffs where the sea breaks loudly."),
]


def dry_near(t, x, z, r=14):
    """The nearest dry, walkable column to (x, z): above sea level and not in inland water."""
    H, water = t["H"], t["water"]
    best, bd = (x, z), 1e9
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            i, j = x + dx + N, z + dz + N
            if 0 <= i < W and 0 <= j < W and H[i, j] >= SEA + 1 and water[i, j] < 0 and dx * dx + dz * dz < bd:
                best, bd = (x + dx, z + dz), dx * dx + dz * dz
    return best


def make_places(t, rng):
    zone, H = t["zone"], t["H"]
    dry = (H >= SEA + 1) & (t["water"] < 0)
    places = {}
    px, pz, _ = t["peak"]
    places["the great mountain"] = {"x": px, "z": pz, "look": "A huge mountain with a white crown of snow, taller than anything else, with a thin stream running down its near face."}
    lk = t["lake"]
    places["the still water"] = {"x": lk["cx"], "z": lk["cz"], "look": "A wide quiet lake in the middle of the land, so still that the sky lies in it."}
    sx, sy, sz = t["spring"]
    places["the cold spring"] = {"x": sx, "z": sz, "look": "High on the mountain, where water first comes out of the cold stone and begins its long run down to the lake."}
    places["the place of waking"] = {"x": 0, "z": t["CLEAR_Z"], "look": "A smooth clearing of short grass a little above the sand, with the whole land opening out ahead."}
    places["the pale shore"] = {"x": 0, "z": t["S0"] - 2, "look": "A long gentle shore of pale sand where the sea comes and goes and the whales sing beyond."}
    for name, zn, look in PLACE_ZONES:
        a = anchor((zone == ZI[zn]) & dry)
        if a is not None:
            places[name] = {"x": a[0], "z": a[1], "look": look}
    if t["rivers"]:
        longest = max(t["rivers"], key=lambda r: len(r["p"]))
        mid = longest["p"][int(len(longest["p"]) * 0.55)]
        mx_, mz_ = dry_near(t, int(mid[0]), int(mid[1]))
        places["the long river"] = {"x": mx_, "z": mz_, "look": "A clear river that begins in the mountains and winds a long way down, falling a step at a time, to the sea."}
    hi = [l for l in t["lakes"] if l.get("w", 0) > SEA]
    if hi:
        l = max(hi, key=lambda q: q["w"])
        hx_, hz_ = dry_near(t, int(l["cx"]), int(l["cz"]), 20)
        places["the high pool"] = {"x": hx_, "z": hz_, "look": "A small round lake high in the hills, cold and clear, with the sky and the stones upside down in it."}
    if t["cave_entrances"]:
        e = t["cave_entrances"][len(t["cave_entrances"]) // 2]
        places["the dark mouth"] = {"x": e[0], "z": e[2], "look": "A black opening in the hillside, cool air breathing out of it, leading down into the rock."}
    return places


# ------------------------------------------------------------------ 8. checks

BANNED = ("biome", "block", "spawn", "pixel", "game", "minecraft", "mob", "server", "player", "texture", "voxel")


def validate(t):
    """Human readable problems; empty when every constraint holds."""
    P = []
    H, water, zone = t["H"], t["water"], t["zone"]
    X, Z = grid()
    R = np.hypot(X, Z)
    S0, CZ = t["S0"], t["CLEAR_Z"]
    if H.shape != (W, W) or zone.shape != (W, W) or water.shape != (W, W):
        return ["array shapes are not 681 x 681"]
    if H.min() < FLOOR:
        P.append(f"H dips below FLOOR ({H.min()})")
    if int(zone.max()) >= len(ZONES):
        P.append("zone index out of range")
    # --- land extent and the sea around it
    land = H >= SEA
    if R[land].max() > 320:
        P.append(f"land reaches radius {R[land].max():.0f} (> 320)")
    dland = edt(land, 70)
    far = dland >= 45
    bad = int(((H != FLOOR) & far).sum())
    if bad:
        P.append(f"{bad} sea columns >= 45 blocks from land are not at FLOOR")
    ref = H[N - 30:N + 31, S0 + 12 + N]
    if ref.max() > SEA - 15:
        P.append(f"sea 12 blocks off the stage shore is only {SEA - ref.max()} deep")
    # --- the stage shore
    if not 250 <= S0 <= 300:
        P.append(f"S0 = {S0} outside 250..300")
    if zone[N, S0 + N] not in (ZI["beach"],):
        P.append(f"shore at x=0 is zone {ZONES[zone[N, S0 + N]]}, not beach")
    if H[N, S0 + N] != SEA or H[N, S0 + 1 + N] >= SEA:
        P.append("S0 is not the last land column on x = 0")
    if H[N, S0 - 12 + N] - H[N, S0 + N] > 6 or np.abs(np.diff(H[N, S0 - 12 + N:S0 + 1 + N].astype(int))).max() > 1:
        P.append("the stage beach is not gentle")
    # --- the clearing
    rc = np.hypot(X, Z - CZ)
    if CZ != S0 - 45:
        P.append("CLEAR_Z != S0 - 45")
    if not (H[rc <= CLEAR_R_IN] == CLEAR_Y).all():
        P.append("clearing is not flat at 68")
    ring = (rc > CLEAR_R_IN) & (rc <= CLEAR_R_OUT)
    if np.abs(np.diff(H[N, CZ - 22 + N:CZ + 23 + N].astype(int))).max() > 3:
        P.append("clearing blend is not smooth")
    if (water[rc <= CLEAR_R_OUT] >= 0).any() or (H[rc <= CLEAR_R_OUT] < SEA).any():
        P.append("water in the clearing")
    if (zone[rc <= CLEAR_R_OUT] != ZI["plains"]).any():
        P.append("clearing is not plains")
    # --- the meadow
    mz0, mz1 = CZ - 85, CZ
    mx = slice(N - 33, N + 34)
    mH = H[mx, mz0 + N:mz1 + 1 + N]
    if mH.min() < 66 or mH.max() > 74:
        P.append(f"meadow heights {mH.min()}..{mH.max()} outside 66..74")
    if (water[mx, mz0 + N:mz1 + 1 + N] >= 0).any():
        P.append("water in the meadow")
    if (zone[mx, mz0 + N:mz1 + 1 + N] != ZI["plains"]).any():
        P.append("meadow is not all plains")
    # --- the stage lake (a sea level hollow)
    lab, sizes = components(H < SEA)
    k = lab[N + LAKE_CX, LAKE_CZ + N]
    lk = t["lake"]
    if k == 0:
        P.append("no lake at the lake centre")
    else:
        m = lab == k
        xs, zs = np.nonzero(m)
        wx, wz = xs.max() - xs.min() + 1, zs.max() - zs.min() + 1
        if wx < 60 or wz < 36:
            P.append(f"lake is only {wx} x {wz}")
        if abs((xs.max() + xs.min()) / 2 - N) > 3:
            P.append("lake is not centred on x = 0")
        if H[m].min() < 56 or H[m].max() > 60:
            P.append(f"lake bed {H[m].min()}..{H[m].max()} outside 56..60")
        if zs.max() - N >= CZ - 85:
            P.append("lake is not beyond the meadow")
        if (R[m] < 0).any():
            pass
        lake_s = zs.max() - N
    # --- the great mountain
    pk = np.unravel_index(int(np.argmax(H)), H.shape)
    pkx, pkz, pky = int(pk[0]) - N, int(pk[1]) - N, int(H[pk])
    if t["peak"] != (pkx, pkz, pky):
        P.append("peak is not the highest column")
    if not 170 <= pky <= 190:
        P.append(f"peak height {pky} outside 170..190")
    if abs(pkx) > 3:
        P.append(f"peak is at x={pkx}, not on the x = 0 axis")
    far_peak = np.hypot(X - pkx, Z - pkz) > 40
    if H[far_peak].max() > pky - 8:
        P.append("another summit is within 8 of the great mountain's height")
    if zone[pk] != ZI["frozen_peaks"]:
        P.append("summit is not frozen_peaks (snow cap)")
    # the line of sight from a viewer standing in the clearing (eye y = 70) to the summit must clear the ground
    zz = np.arange(pkz + 8, CZ)
    line = 70.0 + (pky - 70.0) * (CZ - zz) / float(CZ - pkz)
    for xx in (-12, 0, 12):
        if (H[N + xx, zz + N] > line).any():
            zbad = int(zz[np.argmax(H[N + xx, zz + N] - line)])
            P.append(f"ground blocks the view of the peak from the clearing (x={xx}, z={zbad})")
            break
    # --- the corridor
    if k:
        cor = H[N - 12:N + 13, lake_s + 1 + N:S0 + 1 + N]
        if cor.max() > 74:
            P.append(f"corridor reaches {cor.max()} (> 74)")
    # --- the stream
    st, sp = t["stream"], t["spring"]
    if len(st) < 30 or any(x != 0 for x, z in st):
        P.append("stream is not a straight line down x = 0")
    else:
        zs_ = [z for x, z in st]
        if zs_ != list(range(zs_[0], zs_[0] + len(zs_))):
            P.append("stream columns are not listed top to bottom")
        bed = [int(H[N, z + N]) for z in zs_]
        if any(b2 > b1 for b1, b2 in zip(bed, bed[1:])):
            P.append("stream bed rises going downhill")
        run = 0
        for b1, b2 in zip(bed, bed[1:]):
            run = 0 if b2 < b1 else run + 1
            if run > 3:
                P.append("stream has a level stretch of more than 4 columns")
                break
        for z in zs_:
            if H[N - 1, z + N] < H[N, z + N] + 1 or H[N + 1, z + N] < H[N, z + N] + 1:
                P.append(f"stream bank too low at z={z}")
                break
        if H[N, zs_[-1] + 1 + N] >= SEA:
            P.append("stream does not end at the lake")
        if sp != (0, int(H[N, zs_[0] + N]) + 1, zs_[0]):
            P.append("spring is not at the top of the stream")
        if bed[0] < 140:
            P.append("stream starts low on the mountain")
    # --- water containment
    problems = water_problems(H, water)
    P.extend(problems)
    # --- zones
    zr = zone_report(t)
    for z in ZONES:
        tot, big = zr.get(z, (0, 0))
        need = MIN_THIN if z in THIN else MIN_AREA
        if big < need:
            P.append(f"zone {z}: largest patch {big} < {need}")
    for z in ("frozen_peaks", "jagged_peaks", "stony_peaks"):
        m = zone == ZI[z]
        if m.any() and np.percentile(H[m], 5) < 115:
            P.append(f"{z} reaches down to {np.percentile(H[m], 5):.0f}")
    for z in ("swamp", "mangrove_swamp"):
        m = zone == ZI[z]
        if m.any() and np.percentile(H[m], 95) > 67:
            P.append(f"{z} is not low and flat (95th percentile {np.percentile(H[m], 95):.0f})")
    # --- caves
    P.extend(cave_problems(t))
    # --- places
    pl = t["places"]
    if not 15 <= len(pl) <= 25:
        P.append(f"{len(pl)} places (want 15..25)")
    for name, p in pl.items():
        if not all(key in p for key in ("x", "z", "look")):
            P.append(f"place {name} lacks keys")
            continue
        if abs(p["x"]) > N or abs(p["z"]) > N:
            P.append(f"place {name} off the map")
        low = p["look"].lower()
        if any(b in low for b in BANNED):
            P.append(f"place {name} uses a modern or game word")
    return P


def water_problems(H, water):
    """Level and containment of inland water above sea level."""
    out = []
    w = water.astype(np.int32)
    ww = w >= 0
    if not ww.any():
        return ["there is no inland water above sea level"]
    if (H[ww] >= w[ww]).any():
        out.append(f"{int((H[ww] >= w[ww]).sum())} water columns have a bed at or above their surface")
    if (w[ww] <= SEA).any():
        out.append("water entries at or below sea level")
    bad_cols = np.zeros(H.shape, dtype=bool)
    sea_lvl = (H < SEA) & ~ww
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        sh = lambda a, fill: np.roll(np.roll(a, -dx, 0), -dz, 1)
        nw, nH, nsea = sh(w, -1), sh(H.astype(np.int32), 0), sh(sea_lvl, False)
        # neighbours that are also inland water: levels may differ by at most one
        bad_cols |= ww & (nw >= 0) & (np.abs(nw - w) > 1)
        # neighbours that are sea level water: only one block of fall
        bad_cols |= ww & nsea & (w > SEA + 1)
        # dry neighbours: the bank must stand at least one block above the surface
        dry = (nw < 0) & ~nsea
        bad_cols |= ww & dry & (nH < w + 1)
    # the array edge wraps with roll; ignore the border
    bad_cols[0, :] = bad_cols[-1, :] = bad_cols[:, 0] = bad_cols[:, -1] = False
    n = int(bad_cols.sum())
    if n:
        xs, zs = np.nonzero(bad_cols)
        out.append(f"{n} water columns are not contained (e.g. x={xs[0] - N}, z={zs[0] - N}, surface {w[xs[0], zs[0]]})")
    return out


def cave_problems(t):
    out = []
    boxes = t["caves"]
    H, water = t["H"], t["water"]
    if len(boxes) > 60000:
        out.append(f"{len(boxes)} cave boxes (> 60000)")
    if not boxes:
        return ["no caves"]
    wcol = (H < SEA) | (water >= 0)
    for (x, z) in t["stream"]:
        wcol[x + N, z + N] = True
    near = edt(wcol, 12) <= 6.5
    sat = np.pad(np.cumsum(np.cumsum(near.astype(np.int64), 0), 1), ((1, 0), (1, 0)))
    b = np.array(boxes, dtype=np.int64)
    if (b[:, [0, 3]].min() < -N) or (b[:, [0, 3]].max() > N) or (b[:, [2, 5]].min() < -N) or (b[:, [2, 5]].max() > N):
        out.append("cave box outside the stage")
        return out
    if b[:, [1, 4]].min() < FLOOR + 2:
        out.append("cave box too deep")
    x1, x2, z1, z2 = b[:, 0] + N, b[:, 3] + N, b[:, 2] + N, b[:, 5] + N
    cnt = sat[x2 + 1, z2 + 1] - sat[x1, z2 + 1] - sat[x2 + 1, z1] + sat[x1, z1]
    if (cnt > 0).any():
        out.append(f"{int((cnt > 0).sum())} cave boxes are within 6 blocks of water")
    dx = np.maximum(np.maximum(b[:, 0] - 0, 0 - b[:, 3]), 0)
    dz = np.maximum(np.maximum(b[:, 2] - t["CLEAR_Z"], t["CLEAR_Z"] - b[:, 5]), 0)
    if (np.hypot(dx, dz) < 40).any():
        out.append("cave within 40 blocks of the clearing")
    if ((b[:, 0] < 13) & (b[:, 3] > -13) & (b[:, 5] > PEAK_Z)).any():
        out.append("cave under the stage corridor")
    # voxels under the surface: the roof of each box must be below the ground, except at mouths
    ent = t["cave_entrances"]
    if not ent:
        out.append("no cave entrances")
    for (x, y, z) in ent:
        inside = ((b[:, 0] <= x) & (b[:, 3] >= x) & (b[:, 1] <= y) & (b[:, 4] >= y) & (b[:, 2] <= z) & (b[:, 5] >= z)).any()
        if not inside:
            out.append(f"cave entrance ({x},{y},{z}) is not inside a cave box")
            break
    return out


# ------------------------------------------------------------------ preview


def _palette():
    c = {
        "plains": (150, 190, 90), "sunflower_plains": (222, 205, 60), "meadow": (140, 205, 130),
        "forest": (52, 130, 52), "flower_forest": (200, 140, 200), "birch_forest": (170, 205, 120),
        "old_growth_birch_forest": (120, 170, 90), "dark_forest": (30, 80, 40), "dappled_forest": (95, 150, 80),
        "pale_garden": (190, 195, 185), "cherry_grove": (245, 170, 195), "taiga": (60, 110, 90),
        "old_growth_pine_taiga": (80, 100, 60), "old_growth_spruce_taiga": (50, 85, 70), "snowy_taiga": (130, 170, 160),
        "snowy_plains": (235, 240, 245), "ice_spikes": (170, 220, 245), "grove": (190, 215, 205),
        "snowy_slopes": (225, 232, 238), "frozen_peaks": (250, 252, 255), "jagged_peaks": (205, 215, 225),
        "stony_peaks": (170, 165, 160), "windswept_hills": (140, 150, 135), "windswept_forest": (95, 125, 95),
        "windswept_gravelly_hills": (150, 148, 140), "savanna": (190, 180, 90), "savanna_plateau": (165, 150, 70),
        "windswept_savanna": (175, 165, 105), "desert": (235, 215, 140), "badlands": (200, 100, 55),
        "wooded_badlands": (160, 105, 60), "eroded_badlands": (225, 130, 80), "jungle": (20, 150, 40),
        "sparse_jungle": (95, 175, 55), "bamboo_jungle": (110, 200, 90), "swamp": (85, 105, 70),
        "mangrove_swamp": (110, 80, 60), "mushroom_fields": (190, 120, 150), "beach": (238, 228, 175),
        "snowy_beach": (228, 235, 225), "stony_shore": (120, 120, 120), "river": (70, 120, 200),
        "frozen_river": (150, 185, 225), "warm_ocean": (30, 150, 160), "lukewarm_ocean": (30, 110, 170),
        "ocean": (30, 70, 150), "cold_ocean": (35, 60, 130), "frozen_ocean": (120, 150, 190),
    }
    return np.array([c[z] for z in ZONES], dtype=np.float32)


def hillshade(H):
    h = H.astype(np.float32)
    gx, gz = np.gradient(h)
    ve = 1.3
    nx, nz = -gx * ve, -gz * ve
    nrm = np.sqrt(nx * nx + nz * nz + 1.0)
    lx, ly, lz = -0.55, 0.8, -0.45
    sh = (nx * lx + ly + nz * lz) / nrm / math.sqrt(lx * lx + ly * ly + lz * lz)
    return np.clip(0.25 + 0.75 * sh, 0, 1)


def render_map(t, labels=False):
    from PIL import Image, ImageDraw
    H, zone = t["H"], t["zone"]
    pal = _palette()
    rgb = pal[zone]
    shade = hillshade(blur(H, 0.9))
    rgb = rgb * (0.45 + 0.8 * shade[..., None])
    isw = (H < SEA) | (t["water"] >= 0)
    deep = np.clip((SEA - H) / 20.0, 0, 1)
    sea_c = np.stack([60 - 30 * deep, 130 - 60 * deep, 200 - 50 * deep], axis=-1)
    sea_c = np.where((t["water"] >= 0)[..., None], np.array([70, 140, 215], dtype=np.float32), sea_c)
    rgb = np.where(isw[..., None], sea_c, rgb)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb.transpose(1, 0, 2))
    d = ImageDraw.Draw(img)
    for (x, y, z) in t.get("cave_entrances", []):
        px, pz = x + N, z + N
        d.rectangle([px - 2, pz - 2, px + 2, pz + 2], outline=(255, 0, 0), fill=(255, 60, 0))
    px, pz, _ = t["peak"]
    d.polygon([(px + N, pz + N - 6), (px + N - 5, pz + N + 4), (px + N + 5, pz + N + 4)], outline=(0, 0, 0), fill=(255, 255, 0))
    if labels:
        arr = np.asarray(zone)
        for zi in np.unique(arr):
            m = arr == zi
            if m.sum() < 400:
                continue
            xs, zs = np.nonzero(m)
            d.text((xs.mean() - 20, zs.mean()), ZONES[zi][:14], fill=(0, 0, 0))
    return img


def render_profile(t, x=0):
    """Side view along x = `x`: +z (near, where the viewer floats) on the left, -z (far) on the right."""
    from PIL import Image, ImageDraw
    H = t["H"][x + N].astype(np.int32)
    wt = t["water"][x + N].astype(np.int32)
    zn = t["zone"][x + N]
    pal = _palette()
    sx, sy, y0, y1 = 2, 3, 30, 205
    w, h = W * sx, (y1 - y0) * sy
    cols = np.arange(W)[::-1]                                  # pixel column -> index into z (near on the left)
    Hc, wc, zc = np.repeat(H[cols], sx), np.repeat(wt[cols], sx), np.repeat(zn[cols], sx)
    yy = (y1 - 1 - np.arange(h) // sy)[:, None]                # world y of each pixel row
    img = np.zeros((h, w, 3), dtype=np.float32)
    img[:] = np.array([170, 205, 240], dtype=np.float32)
    ground = yy <= Hc[None, :]
    col = pal[zc][None, :, :] * (0.55 + 0.4 * np.clip((yy - 40) / 150.0, 0, 1))[..., None]
    col = np.where((yy >= Hc[None, :] - 2)[..., None], pal[zc][None, :, :] * 0.85, col)
    img = np.where(ground[..., None], col, img)
    sea = (yy > Hc[None, :]) & (yy <= SEA)
    inl = (yy > Hc[None, :]) & (yy <= wc[None, :]) & (wc[None, :] >= 0)
    img = np.where((sea | inl)[..., None], np.array([50, 110, 190], dtype=np.float32), img)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    X0 = lambda z: (N - z) * sx
    for yv in (FLOOR, SEA, 100, 150, 180):
        py = (y1 - 1 - yv) * sy
        d.line([(0, py), (w, py)], fill=(0, 0, 0), width=1)
        d.text((4, py - 11), f"y={yv}", fill=(0, 0, 0))
    marks = [(t["S0"], "shore S0=%d" % t["S0"]), (t["CLEAR_Z"], "clearing z=%d" % t["CLEAR_Z"]),
             (LAKE_CZ, "lake"), (t["peak"][1], "peak y=%d" % t["peak"][2])]
    for z, txt in marks:
        d.line([(X0(z), 0), (X0(z), h)], fill=(200, 0, 0), width=1)
        d.text((X0(z) + 3, 4), txt, fill=(160, 0, 0))
    for z in range(-N, N + 1, 50):
        d.text((X0(z), h - 12), str(z), fill=(0, 0, 0))
    return out


def render_height(t):
    """Hypsometric tint + hillshade, handy for judging landforms without the zone colours."""
    from PIL import Image
    H = t["H"].astype(np.float32)
    stops = [(42, (20, 40, 110)), (61, (70, 140, 200)), (62, (225, 215, 160)), (66, (110, 170, 80)),
             (85, (70, 130, 60)), (105, (150, 125, 80)), (130, (130, 120, 115)), (150, (200, 200, 200)),
             (190, (255, 255, 255))]
    ys = [s[0] for s in stops]
    rgb = np.stack([np.interp(H, ys, [s[1][c] for s in stops]) for c in range(3)], axis=-1)
    rgb = rgb * (0.4 + 0.9 * hillshade(blur(H, 0.9)))[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2))


# ------------------------------------------------------------------ build and report


def build(seed=31):
    """Make the whole stage.  Keys of the result:
    H (int16 [681,681] top solid y), zone (uint8 index into zones), zones (list of zone keys), water (int16 y of the
    top water block of inland water above sea level, else -1), S0, CLEAR_Z, lake {cx,cz,rx,rz}, peak (x,z,y),
    stream [(x,z) top to bottom], spring (x,y,z), caves [(x1,y1,z1,x2,y2,z2)], cave_entrances [(x,y,z)],
    places {name: {x,z,look}}; also rivers, lakes (elevated and sea level), islets, timing notes."""
    t0 = time.time()
    rng = np.random.default_rng(seed)
    X, Z = grid()
    L = land_field(rng, X, Z)
    L, islets = place_islets(rng, L, X, Z)
    Ld = distance_estimate(L)
    # the stage corridor is plains: give the plains cells a bonus there so that their edge falls well outside it
    corr = 70.0 * smooth((82.0 - np.abs(X)) / 34.0) * smooth((Z - (LAKE_CZ - 10)) / 30.0)
    sidx = voronoi(LAND_SEEDS, X, Z, rng, bonus={"plains": corr})
    zone0 = np.array([ZI[s[0]] for s in LAND_SEEDS], dtype=np.uint8)[sidx]
    nb = make_noise(rng, X, Z)
    Hf, cliff, rm, Ueff = build_heights(rng, X, Z, L, Ld, zone0.astype(np.int64), nb)
    Hf, info = stage_features(rng, X, Z, Hf, nb)
    Hf, water, rmask, lmask, rivers, lakes = build_rivers(rng, X, Z, Hf, info, nb)
    tarns = build_tarns(rng, X, Z, Hf, water, lmask, nb, Ueff, Ld, lakes, rivers)
    Hf, sea_lakes = build_sea_lakes(rng, X, Z, Hf, water, nb, Ueff, Ld, lmask)
    H = np.clip(np.rint(Hf), FLOOR, 255).astype(np.int16)
    H, water = repair_levels(H, water)
    H = fix_banks(H, water)
    info["mushroom"] = islets[0][:2] if islets else None
    zone = finish_zones(rng, X, Z, H, water, zone0, rmask, Ld, cliff, Ueff, info, nb)
    boxes, entrances = build_caves(rng, X, Z, H, water, info["stream"], info, Ld)
    pk = np.unravel_index(int(np.argmax(H)), H.shape)
    lm = info["lake_e"] < 1
    xs, zs = np.nonzero(lm)
    t = {"H": H, "zone": zone, "zones": list(ZONES), "water": water,
         "S0": info["S0"], "CLEAR_Z": info["CLEAR_Z"],
         "lake": {"cx": int(round((xs.max() + xs.min()) / 2)) - N, "cz": int(round((zs.max() + zs.min()) / 2)) - N,
                  "rx": int((xs.max() - xs.min() + 1) // 2), "rz": int((zs.max() - zs.min() + 1) // 2)},
         "peak": (int(pk[0]) - N, int(pk[1]) - N, int(H[pk])),
         "stream": info["stream"], "spring": info["spring"],
         "caves": boxes, "cave_entrances": entrances,
         "rivers": rivers, "lakes": lakes + tarns + [dict(l, w=SEA) for l in sea_lakes],
         "rmask": rmask, "islets": islets, "Ld": Ld, "seed": seed}
    t["places"] = make_places(t, rng)
    t["build_seconds"] = time.time() - t0
    return t

def zone_report(t):
    """{zone: (total columns, largest contiguous patch)}"""
    lab, n, vals = label(t["zone"])
    sizes = np.bincount(lab.ravel(), minlength=n)
    out = {}
    for k in range(n):
        z = ZONES[int(vals[k])]
        tot, big = out.get(z, (0, 0))
        out[z] = (tot + int(sizes[k]), max(big, int(sizes[k])))
    return out


def report(t):
    H = t["H"]
    land = H >= SEA
    print(f"size {W} x {W} columns, seed {t['seed']}, built in {t['build_seconds']:.1f}s")
    print(f"land area {int(land.sum())} columns ({100.0 * land.mean():.1f}% of the stage), S0 = {t['S0']}, CLEAR_Z = {t['CLEAR_Z']}")
    lh = H[land]
    bins = [62, 66, 75, 90, 110, 130, 150, 171, 256]
    hist = np.histogram(lh, bins=bins)[0]
    print("land heights  " + "  ".join(f"{a}-{b - 1}: {n}" for a, b, n in zip(bins, bins[1:], hist)) + f"   max {int(H.max())} at {t['peak']}")
    zr = zone_report(t)
    print("zone areas (total / largest patch):")
    line = ""
    for z in ZONES:
        tot, big = zr.get(z, (0, 0))
        line += f"  {z}: {tot}/{big}"
        if len(line) > 100:
            print(line)
            line = ""
    print(line)
    elevated = [l for l in t["lakes"] if l.get("w", 0) > SEA]
    sea_l = [l for l in t["lakes"] if l.get("w", 0) <= SEA]
    wl = sorted({int(l["w"]) for l in elevated})
    print(f"lakes: 1 stage lake + {len(sea_l)} sea level + {len(elevated)} elevated (surfaces y = {wl});  rivers: {len(t['rivers'])}"
          f" (lengths {[len(r['p']) for r in t['rivers']]});  river columns {int(t['rmask'].sum())}")
    print(f"caves: {len(t['caves'])} boxes, {len(t['cave_entrances'])} entrances;  stream: {len(t['stream'])} columns from y={int(H[N, t['stream'][0][1] + N])}"
          f" to y={int(H[N, t['stream'][-1][1] + N])};  places: {len(t['places'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Eden terrain: build, validate, preview")
    ap.add_argument("--preview", default=None, help="write the top-down map here (and terrain_profile.png beside it)")
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--labels", action="store_true", help="write zone names on the map")
    ap.add_argument("--heightmap", default=None, help="also write a tinted, shaded height image")
    a = ap.parse_args(argv)
    t = build(a.seed)
    if a.preview:
        os.makedirs(os.path.dirname(os.path.abspath(a.preview)), exist_ok=True)
        render_map(t, a.labels).save(a.preview)
        render_profile(t).save(os.path.join(os.path.dirname(os.path.abspath(a.preview)), "terrain_profile.png"))
    if a.heightmap:
        render_height(t).save(a.heightmap)
    report(t)
    problems = validate(t)
    print("validate():", "no problems" if not problems else "")
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())