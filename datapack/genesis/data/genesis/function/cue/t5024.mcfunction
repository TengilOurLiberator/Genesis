summon minecraft:cow -73.31 66.05 10.25 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -73.31 66.65 10.25 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -73.31 66.85 10.25 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -73.31 66.25 10.25 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -73.31 66.05 10.25 0.3 0.2 0.3 0.02 10 force
summon minecraft:pig 148.66 83.05 134.45 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:cold"}
particle minecraft:poof 148.66 83.65 134.45 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 148.66 83.85 134.45 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 148.66 83.25 134.45 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 148.66 83.05 134.45 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.cow.ambient ambient @s ~ ~ ~ 1.0 0.9 1.0
