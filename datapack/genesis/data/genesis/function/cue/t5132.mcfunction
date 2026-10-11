summon minecraft:cow 3.50 72.00 0.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof 3.50 72.60 0.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 3.50 72.80 0.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 3.50 72.20 0.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 3.50 72.00 0.50 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.sheep.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -62.459 78.980 0.500
