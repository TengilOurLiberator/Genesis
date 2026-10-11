"""God, the chief of the angels: a figure of wheels, eyes, wings and fire, built from item_display entities.

Pure functions that return lists of command strings (nothing is written or executed here):

    summon(x, y, z, scale=1.0, facing_yaw=90.0)   one item_display per part, tiny, tagged gen.god + gen.god.<part>
    appear(ticks=40, scale=1.0)                    grow to full size (pose at t=0)
    frame(t, scale=1.0, period=40)                 set the NEXT keyframe (pose at t+period); call for t=0,period,2*period..
    vanish(ticks=40)                               collapse to a point of light
    remove()                                       kill every part
    particles(x, y, z, scale=1.0, facing_yaw=90.0) extra radiance, run every few ticks

LOOP is the length of the seamless animation in ticks; period must divide it (10, 20, 40, 60, 80...).

Design space: 1 unit = DESIGN (0.72) blocks at scale 1.0, u = right as the viewer sees it, v = up, w = towards the viewer.
At scale 1.0: wingspan ~80 blocks, wheels 25-30, corona 38, crown tops out ~28 above the centre, rays 110.
The figure's front faces -x (entity yaw 90 = the +z "south" side of the models is turned to face west), so a viewer
standing at smaller x and looking towards +x sees it from the front.

Command line:
    python tools\\god.py                                 self-test, writes work\\god_test.mcfunction
    python tools\\god.py --preview work\\god_preview.png   flat orthographic preview (needs Pillow)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACK_NS = os.path.join(ROOT, "pack", "genesis-resources", "assets", "genesis")

LOOP = 480            # ticks (24 s); everything below turns an integer number of times per LOOP
TAG = "gen.god"
NS = "genesis"
VIEW_RANGE = 16.0     # x 64 blocks x entity-distance setting -> visible out to ~1000 blocks
TINY = 0.001          # "no size" without a degenerate matrix
DESIGN = 0.50         # design units -> blocks, so scale=1.0 gives a wingspan of ~80 blocks
TILT = 32.0          # degrees the whole figure leans back. Not cosmetic: item models are lit by the world's
                      # fixed entity lights (normal-dependent), so a face turned to a horizontal viewer renders at
                      # ~50% brightness; leaning it back until its normal points ~30 deg upwards gives ~95%.
PULSE_CYCLES = 3      # breaths per LOOP
BEAT_CYCLES = 2       # wing beats per LOOP

ID = (0.0, 0.0, 0.0, 1.0)


# ------------------------------------------------------------------ quaternions (x, y, z, w)
def qaxis(axis, deg):
    a = math.radians(deg) / 2.0
    s = math.sin(a)
    v = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    return (v[0] * s, v[1] * s, v[2] * s, math.cos(a))


def qmul(a, b):
    """a * b : apply b first, then a."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q)


def qdot(a, b):
    return sum(x * y for x, y in zip(a, b))


def qchain(*qs):
    out = ID
    for q in qs:
        out = qmul(out, q)
    return qnorm(out)


def qrot(q, v):
    x, y, z, w = q
    # v' = v + 2w(q x v) + 2 q x (q x v)
    t = (2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0]))
    return (v[0] + w * t[0] + (y * t[2] - z * t[1]),
            v[1] + w * t[1] + (z * t[0] - x * t[2]),
            v[2] + w * t[2] + (x * t[1] - y * t[0]))


# ------------------------------------------------------------------ the parts
def _ph(t, cycles, phase=0.0):
    """Angle in radians of something that goes round `cycles` times per LOOP."""
    return 2 * math.pi * cycles * t / LOOP + phase


def _spin(t, revs, phase=0.0):
    """Degrees; revs per LOOP (integer so the loop closes). Kept to <= 2 so a 40-tick keyframe is <= 60 deg."""
    return 360.0 * revs * t / LOOP + phase


class Part:
    def __init__(self, name, k, pos, pose, billboard=False, flat=False):
        self.name = name        # also the model: genesis:god_<name>
        self.k = k              # blocks per model unit at scale 1 (entity scale = 16 * k)
        self.pos = pos          # (u, v, w) of the pivot, in blocks
        self.pose = pose        # t -> (left_rotation, right_rotation, scale_multiplier)
        self.billboard = billboard
        self.flat = flat        # rotation is only a spin/sway about the figure's own axes: pre-stretch to undo TILT

    @property
    def tag(self):
        return "%s.%s" % (TAG, self.name)


def _wheel(name, k, w, tilt, revs, tphase):
    def pose(t):
        a = _ph(t, 1, tphase)
        left = qchain(qaxis("x", tilt * math.sin(a)), qaxis("y", tilt * 1.3 * math.cos(a)))
        return left, qaxis("z", _spin(t, revs)), 1.0
    return Part(name, k, (0.0, 0.0, w), pose, flat=True)


def _gyro(name, k, axis, tilt, revs, sgn):
    def pose(t):
        left = qchain(qaxis("z", tilt), qaxis(axis, _spin(t, 1) * sgn))
        return left, qaxis("z", _spin(t, revs)), 1.0
    return Part(name, k, (0.0, 0.0, 0.0), pose)


def _wing(name, side, k, shoulder, base, amp, fold, phase):
    sgn = 1.0 if side == "r" else -1.0
    u, v, w = shoulder

    def pose(t):
        a = _ph(t, BEAT_CYCLES, phase)
        theta = base + amp * math.sin(a)
        f = fold * math.sin(a + math.pi / 2)
        return qchain(qaxis("z", sgn * theta), qaxis("y", sgn * f)), ID, 1.0
    return Part("wing_%s" % name + "_" + side, k, (sgn * u, v, w), pose)


def _build_parts():
    P = []
    P.append(Part("rays", 4.0, (0.0, 0.0, -14.0), lambda t: (ID, qaxis("z", _spin(t, 1)), 1.0), flat=True))
    P.append(Part("glow", 3.2, (0.0, 0.0, -10.0),
                  lambda t: (ID, ID, 1.0 + 0.06 * math.sin(_ph(t, PULSE_CYCLES))), flat=True))
    P.append(Part("corona", 2.0, (0.0, 0.0, -3.0), lambda t: (ID, qaxis("z", -_spin(t, 1)), 1.0), flat=True))
    P.append(Part("core", 1.25, (0.0, 0.0, 6.0),
                  lambda t: (ID, qaxis("z", _spin(t, 2)), 1.0 + 0.10 * math.sin(_ph(t, PULSE_CYCLES))), flat=True))
    P.append(Part("crown", 1.75, (0.0, 44.0, 0.0),
                  lambda t: (qchain(qaxis("x", 16), qaxis("y", -_spin(t, 1))), ID,
                             1.0 + 0.04 * math.sin(_ph(t, PULSE_CYCLES, 1.0)))))
    P.append(_wheel("wheel_outer", 1.34, 0.0, 5.0, 1, 0.0))
    P.append(_wheel("wheel_mid", 0.94, 2.0, 5.0, -2, 2.1))
    P.append(_wheel("wheel_inner", 0.60, 4.0, 5.0, 2, 4.2))
    P.append(_gyro("gyro_a", 1.68, "y", 28.0, 1, 1.0))
    P.append(_gyro("gyro_b", 1.15, "x", -28.0, -1, -1.0))
    third = 2 * math.pi / 3
    for side in ("r", "l"):
        P.append(_wing("mid", side, 4.40, (10.0, -1.0, -4.0), 2.0, 6.0, 10.0, 0.0))
        P.append(_wing("hi", side, 3.70, (7.0, 8.0, -6.0), 66.0, 6.0, 9.0, third))
        P.append(_wing("lo", side, 3.70, (7.0, -8.0, -5.0), -62.0, 6.0, 9.0, 2 * third))
    # keep a stable order: rays, glow, corona, core, crown, wheels, gyros, wings
    return P


PARTS = _build_parts()
PART_NAMES = [p.name for p in PARTS]


def pulse(t):
    return 1.0 + 0.02 * math.sin(_ph(t, PULSE_CYCLES))


def pose_at(part, t, scale=1.0):
    """(translation, left_rotation, scale_xyz, right_rotation) of a part at loop time t."""
    left, right, mult = part.pose(t)
    p = pulse(t) * scale * DESIGN
    tilt = qaxis("x", -TILT)
    tr = qrot(tilt, tuple(c * p for c in part.pos))
    s = part.k * 16.0 * mult * p
    sy = s / math.cos(math.radians(TILT)) if part.flat else s
    return tr, qchain(tilt, left), (s, sy, s), right


def _aligned(part, t_from, t_to, scale):
    """Pose at t_to with quaternion signs chosen to be in the same hemisphere as the pose at t_from,
    so the client's slerp takes the short way."""
    tr0, l0, s0, r0 = pose_at(part, t_from, scale)
    tr, l, s, r = pose_at(part, t_to, scale)
    if qdot(l0, l) < 0:
        l = tuple(-c for c in l)
    if qdot(r0, r) < 0:
        r = tuple(-c for c in r)
    return tr, l, s, r


# ------------------------------------------------------------------ SNBT helpers
def _f(v):
    v = round(float(v), 6)
    if v == 0:
        v = 0.0
    s = ("%.6f" % v).rstrip("0")
    if s.endswith("."):
        s += "0"
    return s + "f"


def _vec(v):
    return "[" + ",".join(_f(c) for c in v) + "]"


def _transformation(tr, left, scl, right):
    return "{translation:%s,left_rotation:%s,scale:%s,right_rotation:%s}" % (_vec(tr), _vec(left), _vec(scl), _vec(right))


def _coord(c):
    if isinstance(c, str):
        return c
    return ("%.3f" % c).rstrip("0").rstrip(".") if c != int(c) else "%d" % c


def _sel(part):
    return "@e[type=minecraft:item_display,tag=%s,limit=1]" % part.tag


def _merge(part, nbt):
    return "data merge entity %s %s" % (_sel(part), nbt)


# ------------------------------------------------------------------ the API
def summon(x, y, z, scale=1.0, facing_yaw=90.0):
    """Summon every part at (x, y, z) at near-zero size, already in the pose of t=0.
    Wait a tick or two before calling appear() so the client has seen the tiny starting state."""
    cmds = []
    for p in PARTS:
        tr, l, s, r = pose_at(p, 0, scale)
        s = (TINY, TINY, TINY)
        nbt = ("{Tags:[\"%s\",\"%s\"],Rotation:[%s,0.0f],item_display:\"none\","
               "item:{id:\"minecraft:stick\",count:1,components:{\"minecraft:item_model\":\"%s:god_%s\"}},"
               "brightness:{sky:15,block:15},view_range:%s,interpolation_duration:40,%stransformation:%s}") % (
                   TAG, p.tag, _f(facing_yaw), NS, p.name, _f(VIEW_RANGE),
                   "billboard:\"center\"," if p.billboard else "", _transformation(tr, l, s, r))
        cmds.append("summon minecraft:item_display %s %s %s %s" % (_coord(x), _coord(y), _coord(z), nbt))
    return cmds


def appear(ticks=40, scale=1.0):
    cmds = []
    for p in PARTS:
        tr, l, s, r = pose_at(p, 0, scale)
        cmds.append(_merge(p, "{start_interpolation:0,interpolation_duration:%d,transformation:%s}" % (
            ticks, _transformation(tr, l, s, r))))
    return cmds


def frame(t, scale=1.0, period=40):
    """Keyframe for loop time t+period, to be applied at tick t; interpolates over `period` ticks."""
    if LOOP % period:
        raise ValueError("period %d does not divide LOOP %d" % (period, LOOP))
    cmds = []
    for p in PARTS:
        tr, l, s, r = _aligned(p, t, t + period, scale)
        cmds.append(_merge(p, "{start_interpolation:0,interpolation_duration:%d,transformation:%s}" % (
            period, _transformation(tr, l, s, r))))
    return cmds


def vanish(ticks=40):
    """Every part shrinks to a point and slides into the centre."""
    z = _vec((0.0, 0.0, 0.0))
    t = _vec((TINY, TINY, TINY))
    return [_merge(p, "{start_interpolation:0,interpolation_duration:%d,transformation:{translation:%s,scale:%s}}" % (
        ticks, z, t)) for p in PARTS]


def remove():
    return ["kill @e[type=minecraft:item_display,tag=%s]" % TAG]


def particles(x, y, z, scale=1.0, facing_yaw=90.0):
    """Sparks of light around the figure. `force` so they show from far away (normal mode stops at 32 blocks)."""
    yaw = math.radians(facing_yaw)
    right = (math.cos(yaw), 0.0, math.sin(yaw))     # viewer's right
    front = (-math.sin(yaw), 0.0, math.cos(yaw))    # towards the viewer

    scale = scale * DESIGN

    tilt = qaxis("x", -TILT)

    def at(u, v, w):
        u, v, w = qrot(tilt, (u * scale, v * scale, w * scale))
        return (x + right[0] * u + front[0] * w, y + v, z + right[2] * u + front[2] * w)

    def pc(name, pos, spread, speed, count):
        return "particle minecraft:%s %.2f %.2f %.2f %.2f %.2f %.2f %.3f %d force" % (
            (name,) + pos + (spread, spread, spread, speed, count))

    cmds = [pc("end_rod", at(0, 0, 3), 3.5 * scale, 0.08, 14),
            pc("firework", at(0, 0, 2), 1.8 * scale, 0.10, 3)]
    for i in range(10):                              # sparks riding the outer wheel
        a = 2 * math.pi * i / 10
        cmds.append(pc("end_rod", at(23 * math.cos(a), 23 * math.sin(a), 1), 1.2 * scale, 0.03, 2))
    for i in range(8):                               # fire of the corona
        a = 2 * math.pi * (i + 0.5) / 8
        cmds.append(pc("flame", at(30 * math.cos(a), 30 * math.sin(a), -2), 1.6 * scale, 0.02, 2))
    for sgn in (-1, 1):                              # glitter off the wing tips
        for (u, v) in ((34, 2), (24, 24), (24, -22)):
            cmds.append(pc("glow", at(sgn * u, v, -5), 2.2 * scale, 0.04, 2))
    cmds.append(pc("flame", at(0, 38, 0), 3.0 * scale, 0.03, 4))   # crown
    cmds.append(pc("end_rod", at(0, 40, 0), 2.5 * scale, 0.05, 3))
    return cmds


# ------------------------------------------------------------------ validation of command strings
class SnbtError(ValueError):
    pass


def parse_snbt(s, i=0):
    """Tiny strict SNBT parser (compounds, lists, quoted strings, suffixed numbers, bare words). Returns (value, end)."""
    n = len(s)

    def ws(i):
        while i < n and s[i] == " ":
            i += 1
        return i

    def value(i):
        i = ws(i)
        if i >= n:
            raise SnbtError("unexpected end")
        c = s[i]
        if c == "{":
            out = {}
            i = ws(i + 1)
            if s[i] == "}":
                return out, i + 1
            while True:
                i = ws(i)
                if s[i] in "\"'":
                    k, i = string(i)
                else:
                    j = i
                    while j < n and (s[j].isalnum() or s[j] in "_-.+"):
                        j += 1
                    if j == i:
                        raise SnbtError("bad key at %d" % i)
                    k, i = s[i:j], j
                i = ws(i)
                if s[i] != ":":
                    raise SnbtError("expected ':' at %d" % i)
                v, i = value(i + 1)
                out[k] = v
                i = ws(i)
                if s[i] == ",":
                    i += 1
                    continue
                if s[i] == "}":
                    return out, i + 1
                raise SnbtError("expected ',' or '}' at %d (%r)" % (i, s[i:i + 12]))
        if c == "[":
            out = []
            i = ws(i + 1)
            if s[i] == "]":
                return out, i + 1
            while True:
                v, i = value(i)
                out.append(v)
                i = ws(i)
                if s[i] == ",":
                    i += 1
                    continue
                if s[i] == "]":
                    return out, i + 1
                raise SnbtError("expected ',' or ']' at %d" % i)
        if c in "\"'":
            return string(i)
        j = i
        while j < n and s[j] not in ",]} ":
            j += 1
        tok = s[i:j]
        if not tok:
            raise SnbtError("empty value at %d" % i)
        return tok, j

    def string(i):
        q = s[i]
        j = i + 1
        while j < n and s[j] != q:
            j += 2 if s[j] == "\\" else 1
        if j >= n:
            raise SnbtError("unterminated string")
        return ("str", s[i + 1:j]), j + 1

    return value(i)


def _is_float(tok):
    return isinstance(tok, str) and tok.endswith("f") and _numeric(tok[:-1])


def _numeric(t):
    try:
        float(t)
        return "e" not in t.lower() and "n" not in t.lower()
    except ValueError:
        return False


def check_command(cmd):
    """Raise on malformed SNBT; verify floats in transformation arrays carry the f suffix."""
    if "{" not in cmd:
        return
    start = cmd.index("{")
    if cmd[:start].count("[") != cmd[:start].count("]"):
        raise SnbtError("unbalanced selector brackets: " + cmd[:start])
    val, end = parse_snbt(cmd, start)
    if cmd[end:].strip():
        raise SnbtError("trailing text after NBT: %r" % cmd[end:end + 20])
    tr = val.get("transformation")
    if tr is not None:
        for key, size in (("translation", 3), ("left_rotation", 4), ("scale", 3), ("right_rotation", 4)):
            if key in tr:
                arr = tr[key]
                if len(arr) != size or not all(_is_float(x) for x in arr):
                    raise SnbtError("%s must be %d floats with f suffix: %r" % (key, size, arr))
    if "Rotation" in val and not all(_is_float(x) for x in val["Rotation"]):
        raise SnbtError("Rotation floats")
    if "view_range" in val and not _is_float(val["view_range"]):
        raise SnbtError("view_range float")
    return val


# ------------------------------------------------------------------ flat preview
def _load_models():
    import json
    from PIL import Image
    models = {}
    texcache = {}
    for p in PARTS:
        path = os.path.join(PACK_NS, "models", "item", "god_%s.json" % p.name)
        with open(path) as f:
            m = json.load(f)
        texmap = {}
        for key, ref in m["textures"].items():
            ns, rel = ref.split(":")
            fp = os.path.join(PACK_NS, "textures", rel + ".png")
            if fp not in texcache:
                texcache[fp] = Image.open(fp).convert("RGBA")
            texmap[key] = texcache[fp]
        models[p.name] = (m["elements"], texmap)
    return models


def _erot(pt, rot):
    if not rot:
        return pt
    o = rot["origin"]
    a = math.radians(rot["angle"])
    c, s = math.cos(a), math.sin(a)
    x, y, z = pt[0] - o[0], pt[1] - o[1], pt[2] - o[2]
    ax = rot["axis"]
    if ax == "x":
        y, z = y * c - z * s, y * s + z * c
    elif ax == "y":
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def _face_corners(e, name):
    x1, y1, z1 = e["from"]
    x2, y2, z2 = e["to"]
    return {
        "south": [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
        "north": [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
        "up": [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
        "down": [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)],
        "east": [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
        "west": [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
    }[name]


_L0 = (0.2, 1.0, -0.7)
_L1 = (-0.2, 1.0, 0.7)


def _light(world):
    """Brightness the game gives a face (vanilla entity lighting: two fixed world-space lights + 0.4 ambient).
    Local (u, v, w) = (right, up, towards viewer); with yaw 90 the world is (x, y, z) = (-w, v, u)."""
    e1 = [world[1][i] - world[0][i] for i in range(3)]
    e2 = [world[3][i] - world[0][i] for i in range(3)]
    n = (e2[1] * e1[2] - e2[2] * e1[1], e2[2] * e1[0] - e2[0] * e1[2], e2[0] * e1[1] - e2[1] * e1[0])
    nw = (-n[2], n[1], n[0])
    m = math.sqrt(sum(c * c for c in nw)) or 1.0
    acc = 0.4
    for L in (_L0, _L1):
        ln = math.sqrt(sum(c * c for c in L))
        acc += 0.6 * max(0.0, sum(L[i] * nw[i] for i in range(3)) / (ln * m))
    return min(1.0, acc)


def render_view(models, t, scale, size, bg, half=64.0, ss=2):
    """Orthographic front view (viewer on the +w side). Returns an RGB image of size x size."""
    from PIL import Image, ImageChops, ImageDraw
    W = size * ss
    if bg == "sky":
        canvas = Image.new("RGBA", (W, W), (0, 0, 0, 255))
        px = ImageDraw.Draw(canvas)
        for y in range(W):
            tt = y / W
            px.line([(0, y), (W, y)], fill=(int(86 + 80 * tt), int(150 + 62 * tt), 255, 255))
    else:
        canvas = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    sc = W / (2 * half)

    faces = []
    for p in PARTS:
        elements, texmap = models[p.name]
        tr, l, s, r = pose_at(p, t, scale)
        for e in elements:
            rot = e.get("rotation")
            for fname, fd in e["faces"].items():
                corners = [_erot(c, rot) for c in _face_corners(e, fname)]
                world = []
                for c in corners:
                    v = ((c[0] - 8) / 16.0, (c[1] - 8) / 16.0, (c[2] - 8) / 16.0)
                    v = qrot(r, v)
                    v = (v[0] * s[0], v[1] * s[1], v[2] * s[2])
                    v = qrot(l, v)
                    world.append((v[0] + tr[0], v[1] + tr[1], v[2] + tr[2]))
                scr = [(W / 2 + w[0] * sc, W / 2 - w[1] * sc) for w in world]
                area = sum(scr[i][0] * scr[(i + 1) % 4][1] - scr[(i + 1) % 4][0] * scr[i][1] for i in range(4)) / 2
                if area < 0.5:
                    continue
                depth = sum(w[2] for w in world) / 4
                faces.append((depth, scr, fd, texmap[fd["texture"][1:]], _light(world)))
    faces.sort(key=lambda f: f[0])

    for depth, scr, fd, tex, lit in faces:
        xs = [c[0] for c in scr]
        ys = [c[1] for c in scr]
        x0, y0 = max(0, int(min(xs))), max(0, int(min(ys)))
        x1, y1 = min(W, int(max(xs)) + 2), min(W, int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        tl, trr, br, bl = scr
        e1 = (trr[0] - tl[0], trr[1] - tl[1])
        e2 = (bl[0] - tl[0], bl[1] - tl[1])
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-6:
            continue
        tw, th = tex.size
        u1, v1, u2, v2 = [c * (tw if i % 2 == 0 else th) / 16.0 for i, c in enumerate(fd["uv"])]
        # screen -> (a,b) -> texture
        ia = (e2[1] / det, -e2[0] / det)
        ib = (-e1[1] / det, e1[0] / det)
        # a = ia.x*(X-tlx) + ia.y*(Y-tly) ; b = ib.x*(X-tlx) + ib.y*(Y-tly)
        sx, sy = (u2 - u1), (v2 - v1)
        A = sx * ia[0]
        B = sx * ia[1]
        D = sy * ib[0]
        E = sy * ib[1]
        # output pixel (xo,yo) is screen (xo+x0+.5, yo+y0+.5)
        C = u1 + sx * (ia[0] * (x0 + 0.5 - tl[0]) + ia[1] * (y0 + 0.5 - tl[1]))
        F = v1 + sy * (ib[0] * (x0 + 0.5 - tl[0]) + ib[1] * (y0 + 0.5 - tl[1]))
        layer = tex.transform((x1 - x0, y1 - y0), Image.AFFINE, (A, B, C - 0.5 * (A + B), D, E, F - 0.5 * (D + E)),
                              resample=Image.NEAREST)
        if lit < 0.999:
            r_, g_, b_, a_ = layer.split()
            layer = Image.merge("RGBA", (r_.point(lambda v: int(v * lit)), g_.point(lambda v: int(v * lit)),
                                         b_.point(lambda v: int(v * lit)), a_))
        mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(mask).polygon([(c[0] - x0, c[1] - y0) for c in scr], fill=255)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
        canvas.alpha_composite(layer, (x0, y0))
    return canvas.convert("RGB").resize((size, size), Image.LANCZOS)


def preview(path, size=560, phases=(0, 160, 320), scale=1.0):
    from PIL import Image
    models = _load_models()
    rows = ("black", "sky")
    sheet = Image.new("RGB", (size * len(phases), size * len(rows)))
    for ri, bg in enumerate(rows):
        for ci, t in enumerate(phases):
            sheet.paste(render_view(models, t, scale, size, bg), (ci * size, ri * size))
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)
    return path


# ------------------------------------------------------------------ self-test
def selftest():
    import json
    problems = []
    x, y, z = 60, 100, 0
    summ = summon(x, y, z)
    app = appear(40)
    frames = {t: frame(t) for t in range(0, 5 * 40, 40)}
    everything = summ + app + vanish(40) + remove() + particles(x, y, z)
    for t in frames.values():
        everything += t
    for c in everything:
        try:
            check_command(c)
        except SnbtError as e:
            problems.append("%s :: %s" % (e, c[:120]))
        if "e-" in c or "E-" in c:
            problems.append("exponent in " + c[:80])
    for p in PARTS:
        for sub in (("models", "item"), ("items",)):
            fp = os.path.join(PACK_NS, *sub, "god_%s.json" % p.name)
            if not os.path.isfile(fp):
                problems.append("missing " + fp)
    # keyframe steps must stay under 180 degrees so slerp goes the right way
    worst = 0.0
    for p in PARTS:
        for t in range(0, LOOP, 10):
            for which in (1, 3):
                a = pose_at(p, t)[which]
                b = _aligned(p, t, t + 40, 1.0)[which]
                d = abs(qdot(a, b))
                worst = max(worst, 2 * math.degrees(math.acos(min(1.0, d))))
    # the loop must close
    for p in PARTS:
        a = pose_at(p, 0)
        b = pose_at(p, LOOP)
        for i in (0, 2):
            if any(abs(u - v) > 1e-6 for u, v in zip(a[i], b[i])):
                problems.append("loop does not close: " + p.name)
        for i in (1, 3):
            if abs(qdot(a[i], b[i])) < 1 - 1e-9:
                problems.append("loop rotation does not close: " + p.name)
    print("parts: %d  (%s)" % (len(PARTS), ", ".join(PART_NAMES)))
    print("LOOP = %d ticks; commands per frame = %d; summon = %d; appear = %d; particles = %d" % (
        LOOP, len(frame(0)), len(summ), len(app), len(particles(x, y, z))))
    print("largest rotation step per 40-tick keyframe: %.1f degrees" % worst)

    out = os.path.join(ROOT, "work", "god_test.mcfunction")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = ["# God test. Stand at %d %d %d (or anywhere 50-80 blocks WEST of the figure), look east (+x)." % (x - 60, y - 15, z),
             "# The figure is summoned at %d %d %d facing -x. Run each block in order; the waits matter" % (x, y, z),
             "# (a function runs all of this in one tick, so paste block by block, or schedule them).",
             "", "# ---- block 1: summon (tiny)"]
    lines += summ
    lines += ["", "# ---- block 2: wait 2 ticks, then grow over 40 ticks"]
    lines += app
    lines += ["", "# ---- block 3: 42 ticks later start the loop: run frame(t) at tick t = 0, 40, 80, ... (first five below)"]
    for t in sorted(frames):
        lines += ["# tick %d of the loop" % t] + frames[t]
    lines += ["", "# ---- sparkles: repeat every 5 ticks"] + particles(x, y, z)
    lines += ["", "# ---- end: collapse, then remove 40 ticks later"] + vanish(40) + ["# (40 ticks later)"] + remove()
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out)
    if problems:
        print("PROBLEMS:")
        for p in problems[:40]:
            print("  ", p)
        return 1
    print("all %d commands pass the SNBT / model checks" % len(everything))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--preview" in args:
        i = args.index("--preview")
        out = args[i + 1] if i + 1 < len(args) else "work/god_preview.png"
        size = 560
        phases = (0, 160, 320)
        if "--size" in args:
            size = int(args[args.index("--size") + 1])
        if "--phases" in args:
            phases = tuple(int(v) for v in args[args.index("--phases") + 1].split(","))
        print("wrote", preview(out, size, phases))
    else:
        sys.exit(selftest())

