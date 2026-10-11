function genesis:god/spark
summon minecraft:pig -207.50 69.00 -5.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -207.50 69.60 -5.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -207.50 69.80 -5.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -207.50 69.20 -5.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -207.50 69.00 -5.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:mule -180.24 81.05 46.49 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -180.24 81.65 46.49 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -180.24 81.85 46.49 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -180.24 81.25 46.49 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -180.24 81.05 46.49 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -256.518 83.346 0.500
