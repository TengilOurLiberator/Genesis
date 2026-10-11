setblock -9 77 -37 minecraft:air
place feature minecraft:birch -9 77 -37
particle minecraft:happy_villager -9 80 -37 1.5 2.5 1.5 0 30 force
particle minecraft:composter -9 78 -37 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -110.071 85.275 0.500
