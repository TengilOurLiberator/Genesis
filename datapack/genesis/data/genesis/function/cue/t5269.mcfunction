function genesis:god/spark
summon minecraft:sheep 98.68 74.05 165.38 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Color:15b}
particle minecraft:poof 98.68 74.65 165.38 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 98.68 74.85 165.38 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 98.68 74.25 165.38 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 98.68 74.05 165.38 0.3 0.2 0.3 0.02 10 force
summon minecraft:sheep -201.50 68.00 11.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Color:15b}
particle minecraft:poof -201.50 68.60 11.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -201.50 68.80 11.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -201.50 68.20 11.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -201.50 68.00 11.50 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -256.938 83.625 0.500
