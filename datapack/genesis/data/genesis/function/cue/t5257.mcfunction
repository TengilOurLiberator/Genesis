function genesis:god/spark
summon minecraft:sheep -200.40 76.05 -44.34 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Color:0b}
particle minecraft:poof -200.40 76.65 -44.34 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -200.40 76.85 -44.34 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -200.40 76.25 -44.34 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -200.40 76.05 -44.34 0.3 0.2 0.3 0.02 10 force
summon minecraft:mule -179.44 80.05 48.27 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:poof -179.44 80.65 48.27 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -179.44 80.85 48.27 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -179.44 80.25 48.27 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -179.44 80.05 48.27 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -257.737 84.158 0.500
