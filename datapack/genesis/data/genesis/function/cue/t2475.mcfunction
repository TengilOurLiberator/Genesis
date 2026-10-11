setblock -20 67 98 minecraft:air
place feature minecraft:oak -20 67 98
particle minecraft:happy_villager -20 70 98 1.5 2.5 1.5 0 30 force
particle minecraft:composter -20 68 98 1 2 1 0 16 force
setblock -19 69 91 minecraft:air
place feature minecraft:oak -19 69 91
particle minecraft:happy_villager -19 72 91 1.5 2.5 1.5 0 30 force
particle minecraft:composter -19 70 91 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -141.468 99.932 0.500
