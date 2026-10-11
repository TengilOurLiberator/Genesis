function genesis:god/spark
summon minecraft:cat -240.73 70.05 -16.28 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:calico"}
particle minecraft:poof -240.73 70.65 -16.28 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -240.73 70.85 -16.28 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -240.73 70.25 -16.28 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -240.73 70.05 -16.28 0.3 0.2 0.3 0.02 10 force
summon minecraft:wolf 0.69 86.05 41.60 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:woods"}
particle minecraft:poof 0.69 86.65 41.60 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 0.69 86.85 41.60 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 0.69 86.25 41.60 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 0.69 86.05 41.60 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -260.243 85.828 0.500
