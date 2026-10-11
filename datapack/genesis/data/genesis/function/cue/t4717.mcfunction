function genesis:god/spark
summon minecraft:parrot 14.62 109.80 239.35 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:3}
particle minecraft:poof 14.62 110.40 239.35 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager 14.62 110.60 239.35 0.5 0.6 0.5 0 8 force
summon minecraft:chicken -219.47 65.05 -107.54 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -219.47 65.65 -107.54 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -219.47 65.85 -107.54 0.5 0.6 0.5 0 8 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 71.502 0.500
