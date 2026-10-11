summon minecraft:parrot -269.80 83.03 -17.94 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:0}
particle minecraft:poof -269.80 83.63 -17.94 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -269.80 83.83 -17.94 0.5 0.6 0.5 0 8 force
execute as @a at @s run playsound minecraft:entity.parrot.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 71.320 0.500
