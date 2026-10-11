execute as @a at @s run playsound minecraft:ambient.underwater.exit ambient @s ~ ~ ~ 0.7 0.7 0.7
setblock 39 99 0 minecraft:water
particle minecraft:splash 39 100 0 0.5 0.5 0.5 0.2 60 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -167.220 102.881 0.500
