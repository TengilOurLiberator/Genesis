"""Check the look query and the naming without a player: aim from five blocks away at a cow."""
import re, sys

sys.path.insert(0, r"D:\genesis-vr\tools")
from rcon import Rcon

r = Rcon()
r.cmd("forceload add -96 -96 95 95")
pos = re.findall(r"(-?\d+\.\d+)d", r.cmd("data get entity @e[type=minecraft:cow,limit=1,sort=arbitrary] Pos"))
x, y, z = map(float, pos)
print("cow at", x, y, z)
r.cmd(f"execute positioned {x} {y + 5} {z} rotated 0 90 run function genesis:look/start")
print("aimed at it:", r.cmd("scoreboard players get #look gen"), "| steps", r.cmd("scoreboard players get #ray gen"))
r.cmd(f"execute positioned {x + 5} {y + 1.6} {z} facing {x + 10} {y + 9} {z} run function genesis:look/start")
print("aimed away:", r.cmd("scoreboard players get #look gen"))
print(r.cmd('execute as @e[type=minecraft:cow,tag=!gen.whale] run data merge entity @s {CustomName:"Lowing One"}')[:80])
print(r.cmd("data get entity @e[type=minecraft:cow,limit=1] CustomName"))
r.cmd("forceload remove all")
r.cmd("forceload add -32 -32 31 31")
