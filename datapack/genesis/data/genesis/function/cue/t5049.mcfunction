summon minecraft:horse -199.50 68.00 14.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:773}
particle minecraft:poof -199.50 68.60 14.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -199.50 68.80 14.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -199.50 68.20 14.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -199.50 68.00 14.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:horse -144.66 80.05 61.25 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:3}
particle minecraft:poof -144.66 80.65 61.25 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -144.66 80.85 61.25 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -144.66 80.25 61.25 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -144.66 80.05 61.25 0.3 0.2 0.3 0.02 10 force
summon minecraft:frog 97.65 86.05 -204.47 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof 97.65 86.65 -204.47 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 97.65 86.85 -204.47 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 97.65 86.25 -204.47 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 97.65 86.05 -204.47 0.3 0.2 0.3 0.02 10 force
summon minecraft:turtle -108.50 64.00 37.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -108.50 64.60 37.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -108.50 64.80 37.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -108.50 64.20 37.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -108.50 64.00 37.50 0.3 0.2 0.3 0.02 10 force
execute as @a at @s run playsound minecraft:entity.horse.ambient ambient @s ~ ~ ~ 1.0 1.0 1.0
