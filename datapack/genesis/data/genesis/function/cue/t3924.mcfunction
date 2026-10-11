summon minecraft:cod -94.45 57.98 13.67 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -94.45 57.98 13.67 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -94.45 63.20 13.67 0.3 0.1 0.3 0.1 8 force
summon minecraft:tropical_fish -99.34 57.09 -7.17 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -99.34 57.09 -7.17 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -99.34 63.20 -7.17 0.3 0.1 0.3 0.1 8 force
execute as @a at @s run playsound minecraft:entity.dolphin.splash ambient @s ~ ~ ~ 0.8 0.8 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -96.500 64.300 0.500
