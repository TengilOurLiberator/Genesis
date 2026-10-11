"""Draw the skins for Adam and Eve (64x64, classic arms) into the resource pack."""
import os, random
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "pack", "genesis-resources", "assets", "genesis", "textures", "entity")
os.makedirs(OUT, exist_ok=True)

# name -> (top, bottom, right, front, left, back) boxes as (x, y, w, h)
PARTS = {
    "head": ((8, 0, 8, 8), (16, 0, 8, 8), (0, 8, 8, 8), (8, 8, 8, 8), (16, 8, 8, 8), (24, 8, 8, 8)),
    "body": ((20, 16, 8, 4), (28, 16, 8, 4), (16, 20, 4, 12), (20, 20, 8, 12), (28, 20, 4, 12), (32, 20, 8, 12)),
    "rarm": ((44, 16, 4, 4), (48, 16, 4, 4), (40, 20, 4, 12), (44, 20, 4, 12), (48, 20, 4, 12), (52, 20, 4, 12)),
    "larm": ((36, 48, 4, 4), (40, 48, 4, 4), (32, 52, 4, 12), (36, 52, 4, 12), (40, 52, 4, 12), (44, 52, 4, 12)),
    "rleg": ((4, 16, 4, 4), (8, 16, 4, 4), (0, 20, 4, 12), (4, 20, 4, 12), (8, 20, 4, 12), (12, 20, 4, 12)),
    "lleg": ((20, 48, 4, 4), (24, 48, 4, 4), (16, 52, 4, 12), (20, 52, 4, 12), (24, 52, 4, 12), (28, 52, 4, 12)),
}
LEAVES = [(63, 122, 44), (47, 95, 34), (85, 150, 58), (56, 110, 40)]


def shade(c, rnd, amount=10):
    d = rnd.randint(-amount, amount)
    return tuple(max(0, min(255, v + d)) for v in c) + (255,)


def make(name, skin, hair, long_hair, chest):
    rnd = random.Random(name)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()

    def box(b, colour, rows=None, amount=10):
        x, y, w, h = b
        for j in range(h):
            if rows and not (rows[0] <= j < rows[1]):
                continue
            for i in range(w):
                px[x + i, y + j] = shade(colour if not isinstance(colour, list) else rnd.choice(colour), rnd, amount)

    for part in PARTS.values():
        for b in part:
            box(b, skin, amount=6)
    top, bottom, right, front, left, back = PARTS["head"]
    box(top, hair)
    box(back, hair, (0, 8 if long_hair else 6))
    for side in (right, left):
        box(side, hair, (0, 8 if long_hair else 4))
    box(front, hair, (0, 2))
    fx, fy = front[0], front[1]
    if long_hair:                                    # strands framing the face
        for j in range(2, 8):
            px[fx, fy + j] = shade(hair, rnd)
            px[fx + 7, fy + j] = shade(hair, rnd)
    for ex, white in ((2, 1), (5, 6)):               # eyes: white outside, iris inside
        px[fx + white, fy + 4] = (240, 240, 240, 255)
        px[fx + ex, fy + 4] = (58, 40, 28, 255)
    px[fx + 3, fy + 6] = px[fx + 4, fy + 6] = shade(tuple(int(v * 0.72) for v in skin), rnd, 3)
    if not long_hair:                                # a short beard
        for i in range(1, 7):
            px[fx + i, fy + 7] = shade(hair, rnd)
    _, _, bright, bfront, bleft, bback = PARTS["body"]
    for b in (bright, bfront, bleft, bback):
        box(b, LEAVES, (8, 12))                      # leaves about the hips
        if chest:
            box(b, LEAVES, (1, 5))
    if long_hair:
        box(bback, hair, (0, 5))                     # hair falling down the back
    for leg in ("rleg", "lleg"):
        for b in PARTS[leg][2:]:
            box(b, LEAVES, (0, 4))
    img.save(os.path.join(OUT, name + ".png"))


make("eve", (178, 126, 92), (52, 32, 20), True, True)
make("adam", (166, 114, 80), (40, 26, 18), False, False)
print("skins written to", OUT)
