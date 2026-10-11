setblock -16 69 51 minecraft:air
place feature minecraft:cherry -16 69 51
particle minecraft:happy_villager -16 72 51 1.5 2.5 1.5 0 30 force
particle minecraft:composter -16 70 51 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -111.017 85.613 0.500
