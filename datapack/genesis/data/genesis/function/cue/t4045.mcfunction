function genesis:god/spark
summon minecraft:salmon -291.89 56.45 -10.40 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],type:"large"}
particle minecraft:bubble -291.89 56.45 -10.40 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -291.89 63.20 -10.40 0.3 0.1 0.3 0.1 8 force
summon minecraft:tropical_fish -75.33 54.52 -306.22 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"],Variant:65536}
summon minecraft:pufferfish -285.26 56.14 15.32 {Invulnerable:1b,PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -285.26 56.14 15.32 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -285.26 63.20 15.32 0.3 0.1 0.3 0.1 8 force
execute as @a at @s run playsound minecraft:entity.dolphin.splash ambient @s ~ ~ ~ 0.8 0.8 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -319.500 69.000 0.500
