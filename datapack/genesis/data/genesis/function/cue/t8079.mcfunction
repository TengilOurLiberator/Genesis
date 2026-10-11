summon minecraft:chicken -41.50 66.00 -55.50 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -41.50 66.60 -55.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -41.50 66.80 -55.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -41.50 66.20 -55.50 0.4 0.3 0.4 0.1 20 force
execute as @a at @s run playsound minecraft:entity.horse.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
