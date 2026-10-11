"""Draw the textures, item models and item definitions for the God figure into the resource pack.

    D:\\voice-assistant\\.venv\\Scripts\\python.exe tools\\make_god_assets.py     (any Python with Pillow)

Writes (all under pack/genesis-resources/assets/genesis/):
    textures/item/god_*.png     painted here, deterministic (seeded)
    models/item/god_<part>.json  cuboid models, format modelled on vanilla 26.3 block/item models
    items/god_<part>.json        item model definitions ("minecraft:model" -> genesis:item/god_<part>)

Format notes (checked against the 26.3 client jar):
  * elements use "from"/"to" in -16..32, "rotation": {origin, axis, angle} (arbitrary angle; the old
    22.5-degree restriction is gone in 26.x), "light_emission" 0..15, "shade_direction_override".
    The old per-element "shade": false no longer exists; "shade_direction_override": "up" is how vanilla
    (template_fire_*, template_torch) gets uniform full-bright shading.
  * every part is a model WITHOUT parent, so no "display" block is needed (item_display uses context "none").
  * the model is centred on (8,8,8): the entity transformation pivots around that point.
Part geometry is expressed in model units (16 = one block at scale 1); god.py scales them.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = os.path.join(ROOT, "pack", "genesis-resources", "assets", "genesis")
TEX = os.path.join(NS, "textures", "item")
MOD = os.path.join(NS, "models", "item")
ITM = os.path.join(NS, "items")

# every part that god.py animates; the item_model is genesis:god_<part>
PART_NAMES = [
    "rays", "glow", "core", "corona", "crown",
    "wheel_outer", "wheel_mid", "wheel_inner", "gyro_a", "gyro_b",
    "wing_mid_r", "wing_mid_l", "wing_hi_r", "wing_hi_l", "wing_lo_r", "wing_lo_l",
]

# ---------------------------------------------------------------- colour helpers
DARK = (140, 84, 12)
GOLD_D = (214, 146, 30)
GOLD = (252, 196, 60)
GOLD_L = (255, 230, 130)
CREAM = (255, 244, 205)
WHITE = (255, 253, 240)
BG_FILL = (255, 226, 150)  # RGB stored under fully transparent texels (avoids dark mip fringes)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0) if p1 > p0 else 0)
    return stops[-1][1]


FEATHER_RAMP = [(0.0, GOLD_D), (0.3, GOLD), (0.65, GOLD_L), (1.0, WHITE)]
WING_RAMP = [(0.0, GOLD_L), (0.35, CREAM), (0.7, WHITE), (1.0, WHITE)]
FLAME_RAMP = [(0.0, WHITE), (0.35, (255, 236, 150)), (0.7, (255, 176, 40)), (1.0, (232, 92, 12))]


def save(img, name):
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def finish_cutout(img):
    """Hard 0/255 alpha so Minecraft renders it with the cheap cutout layer (no translucent sorting)."""
    alpha = img.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.composite(img.convert("RGB"), Image.new("RGB", img.size, BG_FILL), alpha)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


# ---------------------------------------------------------------- opaque tiles: gold plates, eyes, runes
def gold_plate(w, h, seed, top=(255, 232, 130), bot=(236, 176, 52)):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        base = mix(top, bot, y / max(1, h - 1))
        for x in range(w):
            n = rnd.randint(-7, 7)
            c = [max(0, min(255, v + n)) for v in base]
            px[x, y] = (c[0], c[1], c[2], 255)
    for x in range(w):  # bevel: bright top edge, dark bottom edge
        px[x, 0] = mix(top, WHITE, 0.55) + (255,)
        px[x, h - 1] = mix(bot, DARK, 0.6) + (255,)
    return img


def eye_layer(w, h, cx, cy, ew, eh, ss=8):
    """A watching eye (white almond, amber iris, black pupil, glint) on a transparent layer."""
    big = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def P(x, y):
        return (x * ss, y * ss)

    n = 48
    top, bot = [], []
    for i in range(n + 1):
        s = -1 + 2 * i / n
        k = (1 - s * s) ** 0.7
        top.append(P(cx + s * ew / 2, cy - eh / 2 * k))
        bot.append(P(cx + s * ew / 2, cy + eh / 2 * k * 0.92))
    poly = top + bot[::-1]
    d.polygon(poly, fill=CREAM + (255,))
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    iris = Image.new("RGBA", big.size, (0, 0, 0, 0))
    di = ImageDraw.Draw(iris)
    ir = eh * 0.47
    icx, icy = cx, cy + eh * 0.02
    for frac, col in [(1.0, (110, 52, 0)), (0.86, (186, 98, 8)), (0.66, (250, 164, 24)), (0.42, (255, 214, 84))]:
        r = ir * frac
        di.ellipse([P(icx - r, icy - r), P(icx + r, icy + r)], fill=col + (255,))
    pr = ir * 0.38
    di.ellipse([P(icx - pr, icy - pr), P(icx + pr, icy + pr)], fill=(14, 5, 0, 255))
    gr = ir * 0.16
    gx, gy = icx - ir * 0.34, icy - ir * 0.36
    di.ellipse([P(gx - gr, gy - gr), P(gx + gr, gy + gr)], fill=(255, 255, 255, 255))
    clip = ImageChops.multiply(mask, iris.getchannel("A"))
    big.paste(iris, (0, 0), clip)
    d.line(poly + [poly[0]], fill=(64, 30, 0, 255), width=max(2, int(ss * 0.95)), joint="curve")
    return big.resize((w, h), Image.LANCZOS)


def make_eye_tile(seed=1):
    plate = gold_plate(32, 16, seed)
    eye = eye_layer(32, 16, 16, 8, 24, 11.5)
    plate.alpha_composite(eye)
    return plate


def make_rune_tile(seed=2):
    plate = gold_plate(32, 16, seed, top=(255, 226, 110), bot=(228, 164, 40))
    big = Image.new("RGBA", (32 * 8, 16 * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy = 16 * 8, 8 * 8
    # a white-hot diamond with a dark gold setting and two flanking chevrons
    d.polygon([(cx, cy - 56), (cx + 44, cy), (cx, cy + 56), (cx - 44, cy)], fill=DARK + (255,))
    d.polygon([(cx, cy - 44), (cx + 33, cy), (cx, cy + 44), (cx - 33, cy)], fill=GOLD_L + (255,))
    d.polygon([(cx, cy - 28), (cx + 20, cy), (cx, cy + 28), (cx - 20, cy)], fill=WHITE + (255,))
    for sx in (-1, 1):
        for off in (0, 1):
            x0 = cx + sx * (74 + off * 22)
            d.line([(x0 - sx * 10, cy - 24), (x0 + sx * 10, cy), (x0 - sx * 10, cy + 24)], fill=DARK + (255,), width=7)
    plate.alpha_composite(big.resize((32, 16), Image.LANCZOS))
    return plate


def make_spoke_tile(seed=3):
    img = gold_plate(16, 16, seed, top=(255, 240, 160), bot=(240, 186, 56))
    px = img.load()
    for y in range(16):  # bright centre line
        for x in (7, 8):
            px[x, y] = mix(px[x, y][:3], WHITE, 0.75) + (255,)
        for x in (0, 15):
            px[x, y] = mix(px[x, y][:3], DARK, 0.5) + (255,)
    return img


def make_core_tile():
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5) / 10.5
            px[x, y] = ramp([(0, WHITE), (0.55, WHITE), (0.85, CREAM), (1.0, GOLD_L)], r) + (255,)
    return img


# ---------------------------------------------------------------- cut-out sprites
def feather(d, root, ang_deg, length, wmax, ss, ramp_stops, outline, shaft=True, slices=10, bend=0.0):
    """One feather: a spindle from `root` along ang_deg (0 = right, + = up), turning by `bend` degrees towards the tip."""
    n = 28
    pts = []                      # centreline, with local normal
    x, y = root
    for i in range(n + 1):
        s = i / n
        a = math.radians(ang_deg + bend * s ** 1.4)
        dx, dy = math.cos(a), -math.sin(a)  # image y points down
        if i:
            x += dx * length / n
            y += dy * length / n
        pts.append((x, y, -dy, dx))

    def prof(s):
        return wmax / 2 * (math.sin(math.pi * min(1.0, s) ** 0.78) ** 0.6)

    def edge(i, side, w):
        px_, py_, nx, ny = pts[i]
        return ((px_ + nx * w * side) * ss, (py_ + ny * w * side) * ss)

    outer = [edge(i, 1, prof(i / n)) for i in range(n + 1)] + [edge(i, -1, prof(i / n)) for i in range(n, -1, -1)]
    d.polygon(outer, fill=outline + (255,))
    per = n // slices
    for k in range(slices):
        i0, i1 = k * per, min(n, (k + 1) * per + 1)
        col = ramp(ramp_stops, ((i0 + i1) / 2) / n)
        poly = [edge(i, 1, prof(i / n) * 0.86) for i in range(i0, i1 + 1)] + \
               [edge(i, -1, prof(i / n) * 0.86) for i in range(i1, i0 - 1, -1)]
        d.polygon(poly, fill=col + (255,))
    if shaft:
        i0, i1 = 2, int(n * 0.88)
        d.line([(pts[i][0] * ss, pts[i][1] * ss) for i in range(i0, i1)],
               fill=mix(ramp(ramp_stops, 0.5), WHITE, 0.55) + (255,), width=max(1, int(ss * 0.7)))


def wing_tile(w, h, root, count, ang_hi, ang_lo, lens, wmax, ramp_stops, outline, len_scale=1.0, ss=4, eyes=0,
              seed=0, bend=-14.0, taper=0.55):
    """A swept wing: feathers rooted at `root` (px), angles from ang_hi (leading edge) down to ang_lo,
    longest at the leading edge and shortening towards the body (taper)."""
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # A solid underlay (the wing "hull", a little shorter than the feather tips) keeps the wing readable when the
    # game's mipmaps blur the fine feather gaps away at distance; the feather tips stick out beyond it.
    hull = [root]
    for i in range(count):
        t = i / (count - 1)
        ang = ang_hi + (ang_lo - ang_hi) * t
        L = lens * (1 - taper * t ** 1.3) * len_scale
        x, y = root
        for k in range(1, 29):
            a = math.radians(ang + bend * (k / 28) ** 1.4)
            x += math.cos(a) * L / 28
            y -= math.sin(a) * L / 28
        hull.append((root[0] + (x - root[0]) * 0.84, root[1] + (y - root[1]) * 0.84))
    d.polygon([(px_ * ss, py_ * ss) for px_, py_ in hull], fill=ramp(ramp_stops, 0.35) + (255,))
    for i in range(count):
        t = i / (count - 1)
        ang = ang_hi + (ang_lo - ang_hi) * t
        L = lens * (1 - taper * t ** 1.3) * len_scale
        feather(d, root, ang, L, wmax * (0.92 + 0.16 * math.sin(i * 1.7)), ss, ramp_stops, outline, bend=bend)
    small = img.resize((w, h), Image.LANCZOS)
    if eyes:
        rnd = random.Random(seed)
        for k in range(eyes):
            ex = root[0] + (w - root[0]) * (0.28 + 0.48 * k / max(1, eyes - 1))
            ey = root[1] + (ex - root[0]) * 0.10 + 7 + rnd.randint(-1, 1)
            small.alpha_composite(eye_layer(w, h, ex, ey, 17, 9.5))
    return small


def make_wing_textures():
    """god_wing.png 128x112: tile A (128x64) the main fan, tile B (128x48) the coverts with eyes.
       god_wing_back.png 128x64: a darker, longer fan seen behind.  Slender on purpose: six wings must stay
       distinct from each other when they radiate from one point."""
    tw, ha, hb = 128, 64, 48
    A = wing_tile(tw, ha, (9, 14), 14, 3, -27, 120, 12, WING_RAMP, mix(GOLD, GOLD_D, 0.4), ss=4, bend=-9)
    B = wing_tile(tw, hb, (9, 12), 9, 2, -24, 118, 11, [(0, GOLD_L), (0.4, WHITE), (1, WHITE)],
                  mix(GOLD, GOLD_D, 0.3), len_scale=0.56, ss=4, eyes=3, seed=7, bend=-9, taper=0.45)
    atlas = Image.new("RGBA", (tw, ha + hb), (0, 0, 0, 0))
    atlas.paste(A, (0, 0))
    atlas.paste(B, (0, ha))
    save(finish_cutout(atlas), "god_wing")
    back_ramp = [(0.0, GOLD), (0.4, GOLD_L), (0.8, CREAM), (1.0, CREAM)]
    C = wing_tile(tw, ha, (9, 14), 12, 12, -20, 124, 13, back_ramp, GOLD_D, ss=4, bend=-12)
    save(finish_cutout(C), "god_wing_back")


def flame_poly(cx, cy, r0, r1, base_w, ang_deg, ss, curve=0.0):
    a = math.radians(ang_deg)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    pts_l, pts_r = [], []
    n = 20
    for i in range(n + 1):
        s = i / n
        r = r0 + (r1 - r0) * s
        w = base_w * (1 - s) ** 0.85 * (1 + 0.18 * math.sin(s * 9))
        off = curve * math.sin(s * math.pi) * (r1 - r0)
        c = (cx + dx * r + nx * off, cy + dy * r + ny * off)
        pts_l.append(((c[0] + nx * w) * ss, (c[1] + ny * w) * ss))
        pts_r.append(((c[0] - nx * w) * ss, (c[1] - ny * w) * ss))
    return pts_l + pts_r[::-1]


def make_corona():
    """A ring of flame tongues in the plane of the wheels (128x128, cutout)."""
    ss = 4
    S = 128
    img = Image.new("RGBA", (S * ss, S * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    n = 20
    # back row of dark-gold tongues, then the bright long tongues over them
    for i in range(n):
        ang = 360 * (i + 0.5) / n
        d.polygon(flame_poly(c, c, 38, 56, 6.2, ang, ss, curve=0.12), fill=(206, 96, 12, 255))
    for i in range(n):
        ang = 360 * i / n
        pts = flame_poly(c, c, 36, 63, 7.0, ang, ss, curve=-0.10)
        d.polygon(pts, fill=(255, 150, 28, 255))
        inner = flame_poly(c, c, 37, 55, 4.2, ang, ss, curve=-0.10)
        d.polygon(inner, fill=(255, 214, 90, 255))
        core = flame_poly(c, c, 38, 46, 2.0, ang, ss, curve=-0.10)
        d.polygon(core, fill=(255, 252, 235, 255))
    # gold band the tongues grow from
    d.ellipse([(c - 40) * ss, (c - 40) * ss, (c + 40) * ss, (c + 40) * ss], outline=GOLD_D + (255,), width=5 * ss)
    d.ellipse([(c - 38) * ss, (c - 38) * ss, (c + 38) * ss, (c + 38) * ss], outline=GOLD_L + (255,), width=2 * ss)
    save(finish_cutout(img.resize((S, S), Image.LANCZOS)), "god_corona")


def make_flame():
    ss = 6
    w, h = 32, 64
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # rises from the bottom centre
    layers = [((232, 100, 14), 15, 0.0), ((255, 160, 34), 12, 0.0), ((255, 214, 96), 8.2, 0.0), ((255, 250, 225), 4.2, 0.0)]
    for i, (col, bw, _) in enumerate(layers):
        top = 2 + i * 7
        pts_l, pts_r = [], []
        n = 28
        for k in range(n + 1):
            s = k / n
            y = h - 1 - (h - 1 - top) * s
            wv = bw * (1 - s) ** 0.8 * (1 + 0.16 * math.sin(s * 8 + i))
            sway = 2.4 * math.sin(s * 5.5) * s
            pts_l.append(((16 + sway - wv) * ss, y * ss))
            pts_r.append(((16 + sway + wv) * ss, y * ss))
        d.polygon(pts_l + pts_r[::-1], fill=col + (255,))
    save(finish_cutout(img.resize((w, h), Image.LANCZOS)), "god_flame")


def make_star():
    """The core: a flat white-hot disc with eight needles. Flat on purpose: the game lights faces by their normal
    (dark when they face down), so a tumbling 3D core read as a grey cube; a flat sprite leaning with the rest of
    the figure is always fully lit."""
    ss = 4
    S = 128
    big = Image.new("RGBA", (S * ss, S * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = S / 2 * ss
    for i in range(8):
        ang = math.radians(45 * i)
        ln, hw = (0.99, 7.0) if i % 2 == 0 else (0.66, 5.2)
        L = ln * 63 * ss
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        w = hw * ss
        d.polygon([(c + nx * w, c + ny * w), (c + dx * L, c + dy * L), (c - nx * w, c - ny * w)], fill=CREAM + (255,))
        w2 = w * 0.5
        d.polygon([(c + nx * w2, c + ny * w2), (c + dx * L * 0.8, c + dy * L * 0.8), (c - nx * w2, c - ny * w2)],
                  fill=WHITE + (255,))
    for r, col in ((24, GOLD_L), (21, CREAM), (17, WHITE)):
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], fill=col + (255,))
    save(finish_cutout(big.resize((S, S), Image.LANCZOS)), "god_star")


# ---------------------------------------------------------------- translucent radiance
def make_glow():
    S = 128
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 63.5, y - 63.5) / 64
            if r >= 1:
                px[x, y] = (255, 230, 150, 0)
                continue
            a = 255 * (math.exp(-(r / 0.30) ** 2) * 0.80 + math.exp(-(r / 0.62) ** 2) * 0.55) * (1 - r ** 3)
            col = ramp([(0, WHITE), (0.25, (255, 246, 205)), (0.6, (255, 214, 110)), (1, (255, 178, 50))], r)
            px[x, y] = col + (int(max(0, min(255, a))),)
    save(img, "god_glow")


def make_rays():
    """Opaque white-gold spikes (hard 0/255 alpha). Translucent rays came out dark grey in the game: alpha-blended
    over black/blue and with black RGB bleeding in from the transparent texels in the mip levels."""
    ss = 4
    S = 128
    big = Image.new("RGBA", (S * ss, S * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = S / 2 * ss
    n = 32
    ramp_r = [(0.0, WHITE), (0.35, (255, 236, 150)), (1.0, (255, 196, 56))]
    for i in range(n):
        ang = math.radians(360 * i / n + 7.5)
        if i % 8 == 0:
            ln, hw = 0.99, 6.0
        elif i % 4 == 0:
            ln, hw = 0.86, 4.8
        elif i % 2 == 0:
            ln, hw = 0.70, 4.0
        else:
            ln, hw = 0.52, 3.2
        L = ln * 63 * ss
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        slices = 10
        for k in range(slices):
            s0, s1 = k / slices, (k + 1) / slices
            w0, w1 = hw * ss * (1 - s0), hw * ss * (1 - s1)
            col = ramp(ramp_r, (s0 + s1) / 2)
            d.polygon([(c + dx * L * s0 + nx * w0, c + dy * L * s0 + ny * w0),
                       (c + dx * L * s1 + nx * w1, c + dy * L * s1 + ny * w1),
                       (c + dx * L * s1 - nx * w1, c + dy * L * s1 - ny * w1),
                       (c + dx * L * s0 - nx * w0, c + dy * L * s0 - ny * w0)], fill=col + (255,))
    d.ellipse([c - 9 * ss, c - 9 * ss, c + 9 * ss, c + 9 * ss], fill=WHITE + (255,))
    save(finish_cutout(big.resize((S, S), Image.LANCZOS)), "god_rays")


# ---------------------------------------------------------------- model building
def rn(v):
    v = round(v, 4)
    return int(v) if v == int(v) else v


def face(tex, uv=(0, 0, 16, 16)):
    return {"uv": [rn(u) for u in uv], "texture": "#" + tex}


def el(frm, to, faces, rot=None, origin=(8, 8, 8)):
    d = {"from": [rn(v) for v in frm], "to": [rn(v) for v in to]}
    if rot:
        axis, angle = rot
        d["rotation"] = {"origin": [rn(v) for v in origin], "axis": axis, "angle": rn(angle)}
    d["light_emission"] = 15
    d["shade_direction_override"] = "up"
    d["faces"] = faces
    return d


def quad(x1, y1, x2, y2, z, tex, uv=(0, 0, 16, 16), mirror=False, rot=None, origin=(8, 8, 8)):
    """Flat double-sided element facing +z (south) and -z (north)."""
    u1, v1, u2, v2 = uv
    if mirror:
        u1, u2 = u2, u1
    x1, x2 = min(x1, x2), max(x1, x2)
    # the back face is seen from the other side, so flip its u to keep text/eyes the right way round there
    return el([x1, y1, z], [x2, y2, z],
              {"south": face(tex, (u1, v1, u2, v2)), "north": face(tex, (u2, v1, u1, v2))}, rot, origin)


def write_model(name, textures, elements):
    assert len(elements) < 120, (name, len(elements))
    for e in elements:
        for k in range(3):
            assert -16 <= e["from"][k] <= 32 and -16 <= e["to"][k] <= 32, (name, e)
    os.makedirs(MOD, exist_ok=True)
    data = {"textures": dict({"particle": next(iter(textures.values()))}, **textures), "elements": elements}
    with open(os.path.join(MOD, "god_%s.json" % name), "w") as f:
        json.dump(data, f, indent=2)
    os.makedirs(ITM, exist_ok=True)
    with open(os.path.join(ITM, "god_%s.json" % name), "w") as f:
        json.dump({"model": {"type": "minecraft:model", "model": "genesis:item/god_%s" % name}}, f, indent=2)


def T(name):
    return "genesis:item/" + name


def ring_segments(rc, width, depth, n, front, outer, plain, z=8.0, depth_bias=0.0):
    """n short boxes forming a ring of centreline radius rc around (8,8), in the xy plane."""
    out = []
    length = 2 * (rc + width * 0.25) * math.tan(math.pi / n)
    for i in range(n):
        ang = 360.0 * i / n
        zb = 0.06 * (i % 2) + depth_bias  # alternate depth so the overlapping inner wedges do not z-fight
        frm = [8 - length / 2, 8 + rc - width / 2, z - depth / 2 - zb]
        to = [8 + length / 2, 8 + rc + width / 2, z + depth / 2 + zb]
        faces = {"south": face(front), "north": face(front, (16, 0, 0, 16)), "up": face(outer),
                 "down": face(plain, (0, 0, 8, 8)), "east": face(plain, (0, 0, 4, 4)), "west": face(plain, (0, 0, 4, 4))}
        out.append(el(frm, to, faces, ("z", ang) if ang else None))
    return out


def spokes(inner, outer_r, count, tex, depth=1.6, half=0.75, offset=0.0):
    out = []
    for i in range(count):
        ang = 360.0 * i / count + offset
        frm = [8 - half, 8 + inner, 8 - depth / 2]
        to = [8 + half, 8 + outer_r, 8 + depth / 2]
        faces = {s: face(tex, (0, 0, 16, 16)) for s in ("south", "north", "east", "west", "up", "down")}
        out.append(el(frm, to, faces, ("z", ang) if ang else None))
    return out


def gems(r, count, size, tex, depth, offset_deg=0.0):
    """Little white-hot diamonds (boxes turned 45 degrees) sitting on the rim joints."""
    out = []
    for i in range(count):
        ang = 360.0 * (i + 0.5) / count + offset_deg
        # rotate the placement by `ang` about the centre, then spin the diamond 45 further inside the same element:
        # an element has one rotation only, so the diamond is the box seen under (ang + 45) and placed via origin trick
        cx, cy = 8 + r * math.sin(math.radians(ang)), 8 + r * math.cos(math.radians(ang))
        frm = [cx - size, cy - size, 8 - depth / 2]
        to = [cx + size, cy + size, 8 + depth / 2]
        faces = {s: face(tex) for s in ("south", "north", "east", "west", "up", "down")}
        out.append(el(frm, to, faces, ("z", 45), origin=(cx, cy, 8)))
    return out


def wheel(name, r_out, width, depth, n, front, outer, studs, spoke_count, hub, tex_extra):
    rc = r_out - width / 2
    els = ring_segments(rc, width, depth, n, front, outer, "gold")
    if spoke_count:
        els += spokes(hub, r_out - width, spoke_count, "spoke")
    if hub:
        h = hub
        faces = {s: face("core") for s in ("south", "north", "east", "west", "up", "down")}
        els.append(el([8 - h, 8 - h, 8 - depth * 0.6], [8 + h, 8 + h, 8 + depth * 0.6], faces))
        els.append(el([8 - h, 8 - h, 8 - depth * 0.6 - 0.05], [8 + h, 8 + h, 8 + depth * 0.6 + 0.05], faces, ("z", 45)))
    if studs:
        els += gems(r_out - 1.2, n, 1.5, "core", depth + 1.4)
    tex = {"gold": T("god_spoke"), "spoke": T("god_spoke"), "core": T("god_core"),
           "eye": T("god_eye"), "rune": T("god_rune")}
    tex.update(tex_extra)
    write_model(name, tex, els)


def build_models():
    # --- the three large wheels, concentric and turning against each other
    wheel("wheel_outer", 23.0, 4.2, 3.2, 16, "eye", "eye", True, 8, 3.0, {})
    wheel("wheel_mid", 23.0, 4.8, 3.6, 16, "rune", "eye", True, 8, 2.4, {})
    wheel("wheel_inner", 23.0, 5.2, 3.6, 16, "eye", "rune", True, 4, 4.0, {})
    # --- two gyroscope rings that tumble around the vertical and horizontal axis
    wheel("gyro_a", 23.0, 3.0, 3.6, 16, "eye", "eye", False, 0, 0, {})
    wheel("gyro_b", 23.0, 3.4, 4.0, 16, "rune", "eye", False, 0, 0, {})

    # --- rays and glow (always turned to the viewer by billboard:"center")
    write_model("rays", {"t": T("god_rays")}, [quad(-16, -16, 32, 32, 8, "t")])
    write_model("glow", {"t": T("god_glow")}, [quad(-16, -16, 32, 32, 8, "t")])
    write_model("corona", {"t": T("god_corona")}, [quad(-16, -16, 32, 32, 8, "t")])

    # --- core: flat white-hot star (see make_star)
    write_model("core", {"t": T("god_star")}, [quad(-16, -16, 32, 32, 8, "t")])

    # --- crown of fire: ring of upright flames standing on a band set with eyes
    els = []
    n = 10
    r = 7.5
    for i in range(n):
        ang = 360.0 * i / n
        els.append(quad(8 - 4.2, 3, 8 + 4.2, 19, 8 + r, "flame", rot=("y", ang)))
        # a smaller flame between each pair, standing a little further in
        els.append(quad(8 - 3.0, 3, 8 + 3.0, 14, 8 + r - 1.8, "flame", rot=("y", ang + 18)))
    blen = 2 * (r + 0.4) * math.tan(math.pi / n) + 0.3
    for i in range(n):
        ang = 360.0 * i / n
        faces = {"south": face("eye"), "north": face("eye", (16, 0, 0, 16)), "up": face("gold", (0, 0, 8, 8)),
                 "down": face("gold", (0, 0, 8, 8)), "east": face("gold", (0, 0, 4, 4)), "west": face("gold", (0, 0, 4, 4))}
        els.append(el([8 - blen / 2, 1.2, 8 + r - 1.0], [8 + blen / 2, 4.2, 8 + r + 1.0], faces, ("y", ang)))
    write_model("crown", {"flame": T("god_flame"), "eye": T("god_eye"), "gold": T("god_spoke")}, els)

    # --- wings: three stacked fans (dark back, bright main, covert row with eyes); root sits on the pivot (8,8)
    def wing(name, mirror, length, back_angle, spread=0.0):
        sgn = -1 if mirror else 1
        mx = (lambda x: 16 - x) if mirror else (lambda x: x)
        x0, x1 = mx(6.0), mx(6.0 + length)
        height, hb = 12.0, 9.0                     # 5.33 px per unit, same as the length direction
        y1 = 8 + height * 14 / 64                  # feather roots sit 14 px (of 64) below the tile top / 12 of 48,
        y0 = y1 - height                           # and the root must land on the pivot (8, 8)
        ya1 = 8 + hb * 12 / 48
        ya0 = ya1 - hb
        vsplit = 16.0 * 64 / 112                   # tile A occupies the top 64 of 112 rows
        ang = lambda a: sgn * a
        els = [
            quad(x0, y0, x1, y1, 7.2, "back", (0, 0, 16, 16), mirror, ("z", ang(back_angle))),
            quad(x0, y0, x1, y1, 8.0, "wing", (0, 0, 16, vsplit), mirror, ("z", ang(spread)) if spread else None),
            quad(x0, ya0, x1, ya1, 8.8, "wing", (0, vsplit, 16, 16), mirror, ("z", ang(spread * 0.5)) if spread else None),
        ]
        write_model(name, {"wing": T("god_wing"), "back": T("god_wing_back")}, els)

    for suffix, mirror in (("r", False), ("l", True)):
        wing("wing_mid_" + suffix, mirror, 24.0, 11.0)
        wing("wing_hi_" + suffix, mirror, 24.0, -10.0)
        wing("wing_lo_" + suffix, mirror, 24.0, 10.0)


def make_textures():
    save(make_eye_tile(), "god_eye")
    save(make_rune_tile(), "god_rune")
    save(make_spoke_tile(), "god_spoke")
    save(make_core_tile(), "god_core")
    make_wing_textures()
    make_corona()
    make_flame()
    make_glow()
    make_rays()
    make_star()


# ---------------------------------------------------------------- validation
def validate():
    problems = []
    names = set()
    for fn in sorted(os.listdir(ITM)):
        if not (fn.startswith("god_") and fn.endswith(".json")):
            continue
        names.add(fn[:-5])
        with open(os.path.join(ITM, fn)) as f:
            item = json.load(f)
        ref = item["model"]["model"]
        ns, path = ref.split(":")
        mp = os.path.join(NS, "models", path + ".json")
        if ns != "genesis" or not os.path.isfile(mp):
            problems.append("%s: missing model %s" % (fn, ref))
    for part in PART_NAMES:
        if "god_" + part not in names:
            problems.append("no item definition for part " + part)
    for fn in sorted(os.listdir(MOD)):
        if not (fn.startswith("god_") and fn.endswith(".json")):
            continue
        with open(os.path.join(MOD, fn)) as f:
            m = json.load(f)
        if len(m["elements"]) >= 120:
            problems.append("%s: %d elements" % (fn, len(m["elements"])))
        for ref in m["textures"].values():
            ns, path = ref.split(":")
            if not os.path.isfile(os.path.join(NS, "textures", path + ".png")):
                problems.append("%s: missing texture %s" % (fn, ref))
        for e in m["elements"]:
            for v in e["from"] + e["to"]:
                if not -16 <= v <= 32:
                    problems.append("%s: coordinate %s out of range" % (fn, v))
            for fc in e["faces"].values():
                if fc["texture"][1:] not in m["textures"]:
                    problems.append("%s: face uses unknown texture var %s" % (fn, fc["texture"]))
                if any(not 0 <= u <= 16 for u in fc["uv"]):
                    problems.append("%s: uv out of range %s" % (fn, fc["uv"]))
    for fn in sorted(os.listdir(TEX)):
        if fn.startswith("god_"):
            im = Image.open(os.path.join(TEX, fn))
            if max(im.size) > 128:
                problems.append("%s: %s larger than 128" % (fn, im.size))
    return problems


if __name__ == "__main__":
    make_textures()
    build_models()
    probs = validate()
    n_models = len([f for f in os.listdir(MOD) if f.startswith("god_")])
    print("wrote %d models, %d item definitions, %d textures" % (
        n_models, len([f for f in os.listdir(ITM) if f.startswith("god_")]),
        len([f for f in os.listdir(TEX) if f.startswith("god_")])))
    if probs:
        print("PROBLEMS:")
        for p in probs:
            print("  ", p)
        sys.exit(1)
    print("validation ok")
