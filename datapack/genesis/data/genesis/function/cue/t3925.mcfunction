summon minecraft:cod -104.45 60.11 20.17 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -104.45 60.11 20.17 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -104.45 63.20 20.17 0.3 0.1 0.3 0.1 8 force
summon minecraft:tropical_fish -138.87 60.16 -17.74 {PersistenceRequired:1b,Tags:["gen.made"]}
particle minecraft:bubble -138.87 60.16 -17.74 0.3 0.3 0.3 0.05 12 force
particle minecraft:splash -138.87 63.20 -17.74 0.3 0.1 0.3 0.1 8 force
execute as @a at @s run playsound minecraft:entity.dolphin.splash ambient @s ~ ~ ~ 0.8 0.8 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -122.500 64.300 0.500
