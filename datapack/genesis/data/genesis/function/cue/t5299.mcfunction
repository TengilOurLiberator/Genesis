function genesis:god/spark
summon minecraft:rabbit -207.50 69.00 -1.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],RabbitType:0}
particle minecraft:poof -207.50 69.60 -1.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -207.50 69.80 -1.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -207.50 69.20 -1.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -207.50 69.00 -1.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:bee -214.78 69.76 70.61 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -214.78 70.36 70.61 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -214.78 70.56 70.61 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -214.78 69.96 70.61 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -214.78 69.76 70.61 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -254.761 82.174 0.500
