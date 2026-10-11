setblock -3 68 -86 minecraft:air
place feature minecraft:birch -3 68 -86
particle minecraft:happy_villager -3 71 -86 1.5 2.5 1.5 0 30 force
particle minecraft:composter -3 69 -86 1 2 1 0 16 force
setblock 0 74 68 minecraft:air
place feature minecraft:oak 0 74 68
particle minecraft:happy_villager 0 77 68 1.5 2.5 1.5 0 30 force
particle minecraft:composter 0 75 68 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -139.598 99.205 0.500
