setblock -50 67 19 minecraft:air
place feature minecraft:fancy_oak -50 67 19
particle minecraft:happy_villager -50 70 19 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -101.418 81.945 0.500
