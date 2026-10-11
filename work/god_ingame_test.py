"""Put the God figure in front of the lobby in a silent test client and photograph it, dark and light."""
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
    r.cmd(f"time of genesis:cut set {marks['light'] - 6}")       # black sky, but far things can be seen
    r.cmd(f"gamemode spectator {N}")
    r.cmd(f"tp {N} 1001.5 104 1000.5 -90 -12")
    out = [r.cmd(c) for c in god.summon(X, Y, Z, scale=SCALE)]
    print("summon:", set(o[:40] for o in out))
    time.sleep(0.4)
    out = [r.cmd(c) for c in god.appear(ticks=30, scale=SCALE)]
    print("appear:", set(o[:60] for o in out))
    time.sleep(2.5)
    for i in range(3):
        for c in god.frame(i * 40, scale=SCALE, period=40):
            r.cmd(c)
        for c in god.particles(X, Y, Z, scale=SCALE):
            r.cmd(c)
        time.sleep(2.0)
        vt.shot(f"god_dark_{i}")
    r.cmd(f"tp {N} 1040.5 112 1000.5 -90 -15")                   # close up
    time.sleep(1.5)
    vt.shot("god_dark_close")
    r.cmd(f"tp {N} 1060.5 118 1030.5 180 0")                     # side view
    time.sleep(1.5)
    vt.shot("god_side")
    r.cmd(f"tp {N} 1001.5 104 1000.5 -90 -12")
    r.cmd("time of genesis:cut set 3000")                        # daylight
    for c in god.frame(120, scale=SCALE, period=40):
        r.cmd(c)
    time.sleep(3)
    vt.shot("god_day")
    r.cmd(f"tp {N} 1030.5 112 1000.5 -90 -8")
    time.sleep(1.5)
    vt.shot("god_day_close")
    for c in god.vanish(ticks=20):
        r.cmd(c)
    time.sleep(1.5)
    print("entities before remove:", r.cmd("execute if entity @e[tag=gen.god]"))
    for c in god.remove():
        r.cmd(c)
finally:
    r.cmd("time of genesis:cut set 0")
    client.terminate()

