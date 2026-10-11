function genesis:god/spark
summon minecraft:parrot -272.19 81.33 -10.96 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:1}
particle minecraft:poof -272.19 81.93 -10.96 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -272.19 82.13 -10.96 0.5 0.6 0.5 0 8 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 71.395 0.500
