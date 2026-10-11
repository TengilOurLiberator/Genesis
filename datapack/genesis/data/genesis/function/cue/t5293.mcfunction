function genesis:god/spark
summon minecraft:rabbit -39.29 67.05 -228.23 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],RabbitType:4}
particle minecraft:poof -39.29 67.65 -228.23 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -39.29 67.85 -228.23 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -39.29 67.25 -228.23 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -39.29 67.05 -228.23 0.3 0.2 0.3 0.02 10 force
summon minecraft:bee -14.38 89.25 -59.31 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -14.38 89.85 -59.31 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -14.38 90.05 -59.31 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -14.38 89.45 -59.31 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -14.38 89.25 -59.31 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -255.208 82.472 0.500
