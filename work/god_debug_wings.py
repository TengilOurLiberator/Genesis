"""Diagnose the invisible wings: full figure shot, data dump of a wing, then wings only."""
import json, os, sys, time

sys.path.insert(0, r"D:\genesis-vr\tools")
import visual_test as vt
import god
from rcon import Rcon

os.makedirs(vt.SHOTS, exist_ok=True)
vt.ctypes.windll.user32.SetProcessDPIAware()
marks = json.load(open(r"D:\genesis-vr\work\schedule.json"))["marks"]
client = vt.launch()
r = Rcon()
N = vt.NAME
X, Y, Z, SCALE = 1060, 118, 1000.5, 0.45
try:
    deadline = time.time() + 180
    while N not in r.cmd("list"):
        if time.time() > deadline:
            sys.exit("client did not join")
        time.sleep(2)
    time.sleep(12)
    r.cmd("forceload add 1000 984 1100 1016")
    r.cmd(f"time of genesis:cut set {marks['light'] - 6}")
    r.cmd(f"gamemode spectator {N}")
    r.cmd(f"tp {N} 1001.5 104 1000.5 -90 -12")
    for c in god.summon(X, Y, Z, scale=SCALE):
        r.cmd(c)
    time.sleep(0.4)
    for c in god.appear(ticks=30, scale=SCALE):
        r.cmd(c)
    time.sleep(2.5)
    vt.shot("dbg_full")
    for step, kills in (("noglow", ["glow"]), ("norays", ["rays"]), ("nocorona", ["corona", "crown"])):
        for p in kills:
            r.cmd(f"kill @e[type=minecraft:item_display,tag=gen.god.{p}]")
        time.sleep(1.2)
        vt.shot("dbg_" + step)
    for c in god.remove():
        r.cmd(c)
finally:
    r.cmd("time of genesis:cut set 0")
    client.terminate()

