function genesis:god/spark
summon minecraft:chicken -97.55 85.05 62.72 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -97.55 85.65 62.72 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -97.55 85.85 62.72 0.5 0.6 0.5 0 8 force
summon minecraft:chicken 147.31 94.35 34.73 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:cold"}
particle minecraft:poof 147.31 94.95 34.73 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 147.31 95.15 34.73 0.5 0.6 0.5 0 8 force
summon minecraft:parrot -271.01 75.50 -14.60 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:4}
particle minecraft:poof -271.01 76.10 -14.60 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -271.01 76.30 -14.60 0.5 0.6 0.5 0 8 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 71.601 0.500
