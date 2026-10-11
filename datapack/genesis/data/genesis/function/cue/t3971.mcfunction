setblock -30 69 -7 minecraft:air
place feature minecraft:cherry -30 69 -7
particle minecraft:happy_villager -30 72 -7 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -98.929 80.286 0.500
