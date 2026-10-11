setblock -24 66 -91 minecraft:air
place feature minecraft:birch -24 66 -91
particle minecraft:happy_villager -24 69 -91 1.5 2.5 1.5 0 30 force
particle minecraft:composter -24 67 -91 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -141.801 100.061 0.500
