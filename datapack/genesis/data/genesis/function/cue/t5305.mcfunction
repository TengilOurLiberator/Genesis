function genesis:god/spark
summon minecraft:rabbit -204.50 68.00 -26.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],RabbitType:0}
particle minecraft:poof -204.50 68.60 -26.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -204.50 68.80 -26.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -204.50 68.20 -26.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -204.50 68.00 -26.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:turtle 227.52 64.05 120.60 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof 227.52 64.65 120.60 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 227.52 64.85 120.60 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 227.52 64.25 120.60 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 227.52 64.05 120.60 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -254.313 81.876 0.500
