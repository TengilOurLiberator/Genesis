"""Try profile formats for a mannequin with a resource-pack skin and print what the server keeps."""
import sys

sys.path.insert(0, r"D:\genesis-vr\tools")
from rcon import Rcon

r = Rcon()
for prof in ['{texture:"genesis:entity/eve"}', '{texture:"genesis:entity/eve",model:"slim"}',
             '{name:"Eve",texture:"genesis:entity/eve"}', '{skin:"genesis:entity/eve"}']:
    print(prof, "->", r.cmd('summon minecraft:mannequin 0 120 0 {Tags:["gen.t"],NoGravity:1b,profile:%s}' % prof)[:200])
    print("   ", r.cmd("data get entity @e[tag=gen.t,limit=1] profile")[:200])
    r.cmd("kill @e[tag=gen.t]")
print(r.cmd("data get entity @e[tag=gen.companion,limit=1]")[:600])
