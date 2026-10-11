function genesis:god/spark
summon minecraft:fox 169.21 78.35 -53.27 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Type:"snow"}
particle minecraft:poof 169.21 78.95 -53.27 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 169.21 79.15 -53.27 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 169.21 78.55 -53.27 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 169.21 78.35 -53.27 0.3 0.2 0.3 0.02 10 force
summon minecraft:panda 15.51 81.05 250.31 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],MainGene:"lazy",HiddenGene:"lazy"}
particle minecraft:poof 15.51 81.65 250.31 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 15.51 81.85 250.31 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} 15.51 81.25 250.31 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume 15.51 81.05 250.31 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -259.887 85.591 0.500
