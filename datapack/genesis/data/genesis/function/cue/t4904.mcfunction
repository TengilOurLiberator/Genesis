summon minecraft:cow -36.50 72.00 4.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -36.50 72.60 4.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -36.50 72.80 4.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -36.50 72.20 4.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -36.50 72.00 4.50 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.cow.ambient ambient @s ~ ~ ~ 1.0 0.9 1.0
