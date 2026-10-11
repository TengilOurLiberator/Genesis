summon minecraft:cow -12.50 71.00 3.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -12.50 71.60 3.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -12.50 71.80 3.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -12.50 71.20 3.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -12.50 71.00 3.50 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.sheep.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -96.051 84.367 0.500
