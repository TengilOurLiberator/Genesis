"""Prepare a Minecraft game folder for Genesis: resource pack, options, server list, and (optionally) mods.

    python tools\\setup_client.py D:\\genesis-vr\\game --mods
"""
import argparse, os, shutil, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(os.environ["APPDATA"], ".minecraft")
PACK = "genesis-resources"

ap = argparse.ArgumentParser()
ap.add_argument("game_dir")
ap.add_argument("--mods", action="store_true", help="copy Fabric API and Vivecraft into mods")
args = ap.parse_args()
game = args.game_dir
os.makedirs(game, exist_ok=True)

# resource pack: the narration in the god voice only
src = os.path.join(ROOT, "pack", PACK)
dst = os.path.join(game, "resourcepacks", PACK)
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(src, dst)

# options: start from the player's own, then set what the piece needs
wanted = {"resourcePacks": f'["vanilla","fabric","file/{PACK}"]', "onboardAccessibility": "false",
          "skipMultiplayerWarning": "true", "joinedFirstServer": "true", "tutorialStep": "none",
          "pauseOnLostFocus": "false", "soundCategory_voice": "1.0",
          # as far and as fine as the game allows: the piece is about seeing a whole world appear
          "renderDistance": "32", "simulationDistance": "16", "entityDistanceScaling": "5.0", "biomeBlendRadius": "7",
          "cloudRange": "128", "particles": "0", "graphicsPreset": "\"custom\"", "mipmapLevels": "4", "entityShadows": "true"}
lines, seen = [], set()
base = os.path.join(game, "options.txt") if os.path.exists(os.path.join(game, "options.txt")) else os.path.join(MC, "options.txt")
if os.path.exists(base):
    for line in open(base, encoding="utf-8"):
        key = line.split(":", 1)[0]
        if key in wanted:
            line = f"{key}:{wanted[key]}\n"
            seen.add(key)
        lines.append(line)
lines += [f"{k}:{v}\n" for k, v in wanted.items() if k not in seen]
open(os.path.join(game, "options.txt"), "w", encoding="utf-8").writelines(lines)


# server list (uncompressed NBT): one entry, the local Genesis server
def s(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


entry = b"\x08" + s("name") + s("Genesis") + b"\x08" + s("ip") + s("localhost") + b"\x00"
nbt = b"\x0a" + s("") + b"\x09" + s("servers") + b"\x0a" + struct.pack(">i", 1) + entry + b"\x00"
open(os.path.join(game, "servers.dat"), "wb").write(nbt)

if args.mods:
    os.makedirs(os.path.join(game, "mods"), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "downloads")):
        if f.startswith(("fabric-api", "vivecraft")):
            shutil.copy2(os.path.join(ROOT, "downloads", f), os.path.join(game, "mods", f))
print("ready:", game, os.listdir(game))
