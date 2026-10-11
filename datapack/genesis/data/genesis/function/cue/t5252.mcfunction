summon minecraft:pig -14.54 83.05 129.35 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -14.54 83.65 129.35 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -14.54 83.85 129.35 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -14.54 83.25 129.35 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -14.54 83.05 129.35 0.3 0.2 0.3 0.02 10 force
summon minecraft:donkey -18.70 80.05 63.51 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -18.70 80.65 63.51 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -18.70 80.85 63.51 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -18.70 80.25 63.51 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -18.70 80.05 63.51 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.sheep.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -258.051 84.367 0.500
