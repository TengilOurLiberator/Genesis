"""Probe how bright a flat white panel renders in the game when tilted back by 0/20/40/60 degrees (and as a billboard)."""
import json, math, os, sys, time

sys.path.insert(0, r"D:\genesis-vr\tools")
import visual_test as vt
import god
from rcon import Rcon

vt.ctypes.windll.user32.SetProcessDPIAware()
marks = json.load(open(r"D:\genesis-vr\work\schedule.json"))["marks"]
client = vt.launch()
r = Rcon()
N = vt.NAME
X, Y, Z = 1060, 118, 1000.5
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
    r.cmd("kill @e[tag=gen.probe]")
    panels = [(-22, 0, False), (-11, 20, False), (0, 40, False), (11, 60, False), (22, 0, True)]
    for dz, tilt, bb in panels:
        q = god.qaxis("x", -tilt)
        nbt = ("{Tags:[\"gen.probe\"],Rotation:[90.0f,0.0f],item_display:\"none\","
               "item:{id:\"minecraft:stick\",count:1,components:{\"minecraft:item_model\":\"genesis:god_rays\"}},"
               "brightness:{sky:15,block:15},view_range:16.0f,%s"
               "transformation:{translation:[0f,0f,0f],left_rotation:%s,scale:[3f,3f,3f],right_rotation:[0f,0f,0f,1f]}}") % (
                   'billboard:"center",' if bb else "", god._vec(q))
        print(r.cmd(f"summon minecraft:item_display {X} {Y} {Z + dz} {nbt}")[:50])
    time.sleep(3)
    vt.shot("probe_light")
    r.cmd("kill @e[tag=gen.probe]")
finally:
    r.cmd("time of genesis:cut set 0")
    client.terminate()
