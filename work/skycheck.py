"""Join the finished world in a desktop client and photograph the sky at set clock times, and the companion."""
import os, sys, time

sys.path.insert(0, r"D:\genesis-vr\tools")
import visual_test as vt
from rcon import Rcon

os.makedirs(vt.SHOTS, exist_ok=True)
vt.ctypes.windll.user32.SetProcessDPIAware()
client = vt.launch()
r = Rcon()
N = vt.NAME
try:
    deadline = time.time() + 180
    while N not in r.cmd("list"):
        if time.time() > deadline:
            sys.exit("client did not join")
        time.sleep(2)
    time.sleep(12)
    r.cmd("time of genesis:day pause")
    # the companion, close up, front and back
    r.cmd('kill @e[tag=gen.companion]')
    r.cmd('summon minecraft:mannequin -0.5 69 2.5 {Tags:["gen.companion","gen.eve"],CustomName:"Eve",Invulnerable:1b,profile:{texture:"genesis:entity/eve"}}')
    r.cmd('summon minecraft:mannequin -0.5 69 -1.5 {Tags:["gen.adamtest"],CustomName:"Adam",Invulnerable:1b,Rotation:[90f,0f],profile:{texture:"genesis:entity/adam"}}')
    r.cmd("time of genesis:day set 78000")
    r.cmd(f"tp {N} -4.5 69 0.5 -90 5")
    time.sleep(3)
    vt.shot("s_people_front")
    r.cmd(f"tp {N} 3.5 69 0.5 90 5")
    time.sleep(3)
    vt.shot("s_people_back")
    r.cmd("kill @e[tag=gen.adamtest]")
    # the sky, from west of the island looking east
    r.cmd(f"gamemode spectator {N}")
    r.cmd(f"tp {N} -104.5 84 0.5 -90 -8")
    for name, t in [("s1_noon_sunless", 6000), ("s2_predawn", 47300), ("s2_sunrise", 48500), ("s2_morning", 50500)]:
        r.cmd(f"time of genesis:day set {t}")
        time.sleep(3)
        vt.shot(name)
    r.cmd(f"tp {N} -104.5 84 0.5 -90 -35")
    for name, t in [("s2_moonrise", 62500), ("s2_stars", 67000)]:
        r.cmd(f"time of genesis:day set {t}")
        time.sleep(3)
        vt.shot(name)
    # does the client follow a fast clock? sunrise to noon in four seconds, photographed as it goes
    r.cmd(f"tp {N} -104.5 84 0.5 -90 -20")
    r.cmd("time of genesis:day set 47500")
    time.sleep(2)
    r.cmd("time of genesis:day rate 81.25")
    r.cmd("time of genesis:day resume")
    for i in range(3):
        time.sleep(1.0)
        vt.shot(f"s3_lapse_{i + 1}s")
    r.cmd("time of genesis:day pause")
    # the opening darkness and the lobby light level
    r.cmd("time of genesis:day set 6000")
    r.cmd("time of genesis:cut set 300")
    time.sleep(3)
    vt.shot("s4_darkness")
finally:
    r.cmd("time of genesis:cut set 20000")
    r.cmd("time of genesis:day set 78000")
    r.cmd("time of genesis:day rate 1")
    r.cmd("time of genesis:day resume")
    client.terminate()
