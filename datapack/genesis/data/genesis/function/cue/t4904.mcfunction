summon minecraft:cow -19.50 70.00 10.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -19.50 70.60 10.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -19.50 70.80 10.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -19.50 70.20 10.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -19.50 70.00 10.50 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.cow.ambient ambient @s ~ ~ ~ 1.0 0.9 1.0
