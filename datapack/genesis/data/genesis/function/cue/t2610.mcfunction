setblock 79 98 15 minecraft:air
place feature minecraft:spruce 79 98 15
particle minecraft:happy_villager 79 101 15 1.5 2.5 1.5 0 30 force
particle minecraft:composter 79 99 15 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.501 98.000 0.500
