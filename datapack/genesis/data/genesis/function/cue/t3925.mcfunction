summon minecraft:cod -97.02 57.03 -0.74 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -97.02 57.03 -0.74 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -97.02 63.20 -0.74 0.3 0.1 0.3 0.1 8 force
summon minecraft:tropical_fish -104.72 58.20 21.75 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -104.72 58.20 21.75 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -104.72 63.20 21.75 0.3 0.1 0.3 0.1 8 force
execute as @a at @s run playsound minecraft:entity.dolphin.splash ambient @s ~ ~ ~ 0.8 0.8 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -96.500 64.300 0.500
