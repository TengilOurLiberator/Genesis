summon minecraft:parrot -61.56 75.03 24.89 {PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -61.56 75.63 24.89 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -61.56 75.83 24.89 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound minecraft:entity.parrot.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -96.500 68.708 0.500
