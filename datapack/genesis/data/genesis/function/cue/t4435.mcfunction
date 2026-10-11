function genesis:god/spark
summon minecraft:chicken -221.50 70.00 15.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -221.50 70.60 15.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -221.50 70.80 15.50 0.5 0.6 0.5 0 8 force
summon minecraft:parrot -288.10 72.27 9.79 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:1}
particle minecraft:poof -288.10 72.87 9.79 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -288.10 73.07 9.79 0.5 0.6 0.5 0 8 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 66.408 0.500
