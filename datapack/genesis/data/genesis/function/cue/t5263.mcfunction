function genesis:god/spark
summon minecraft:horse -190.50 67.00 24.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:6}
particle minecraft:poof -190.50 67.60 24.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -190.50 67.80 24.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -190.50 67.20 24.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -190.50 67.00 24.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:cow -76.40 64.05 16.30 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -76.40 64.65 16.30 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -76.40 64.85 16.30 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -76.40 64.25 16.30 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -76.40 64.05 16.30 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -257.345 83.896 0.500
