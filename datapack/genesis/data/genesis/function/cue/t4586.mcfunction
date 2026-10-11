summon minecraft:parrot -62.04 76.22 -18.12 {PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -62.04 76.82 -18.12 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -62.04 77.02 -18.12 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound minecraft:entity.parrot.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -96.500 68.708 0.500
