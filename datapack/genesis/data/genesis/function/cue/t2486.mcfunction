setblock -13 67 101 minecraft:air
place feature minecraft:oak -13 67 101
particle minecraft:happy_villager -13 70 101 1.5 2.5 1.5 0 30 force
particle minecraft:composter -13 68 101 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -140.764 99.658 0.500
