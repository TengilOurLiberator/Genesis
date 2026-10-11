setblock -29 68 20 minecraft:air
place feature minecraft:fancy_oak -29 68 20
particle minecraft:happy_villager -29 71 20 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -99.232 80.488 0.500
