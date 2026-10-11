setblock -6 68 -56 minecraft:air
place feature minecraft:oak -6 68 -56
particle minecraft:happy_villager -6 71 -56 1.5 2.5 1.5 0 30 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.9 0.7 0.9
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -102.388 82.592 0.500
