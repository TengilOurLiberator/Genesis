function genesis:god/f10
summon minecraft:sheep -183.50 67.00 1.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Color:12b}
particle minecraft:poof -183.50 67.60 1.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -183.50 67.80 1.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -183.50 67.20 1.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -183.50 67.00 1.50 0.3 0.2 0.3 0.02 10 force
summon minecraft:cow -197.50 68.00 -2.50 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],variant:"minecraft:temperate"}
particle minecraft:poof -197.50 68.60 -2.50 0.4 0.5 0.4 0.02 14 force
particle minecraft:happy_villager -197.50 68.80 -2.50 0.5 0.6 0.5 0 8 force
particle minecraft:block{block_state:"minecraft:dirt"} -197.50 68.20 -2.50 0.4 0.3 0.4 0.1 24 force
particle minecraft:dust_plume -197.50 68.00 -2.50 0.3 0.2 0.3 0.02 10 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -256.659 83.440 0.500
