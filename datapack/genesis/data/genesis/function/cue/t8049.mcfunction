summon minecraft:cow -27.50 71.00 -31.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -27.50 71.60 -31.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -27.50 71.80 -31.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -27.50 71.20 -31.50 0.4 0.3 0.4 0.1 20 force
summon minecraft:frog -35.50 67.00 -44.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -35.50 67.60 -44.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -35.50 67.80 -44.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -35.50 67.20 -44.50 0.4 0.3 0.4 0.1 20 force
execute as @a at @s run playsound minecraft:entity.cow.ambient ambient @s ~ ~ ~ 1.0 0.9 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -62.500 76.000 0.500
