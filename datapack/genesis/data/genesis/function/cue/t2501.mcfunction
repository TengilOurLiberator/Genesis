setblock -5 77 61 minecraft:air
place feature minecraft:oak -5 77 61
particle minecraft:happy_villager -5 80 61 1.5 2.5 1.5 0 30 force
particle minecraft:composter -5 78 61 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -139.875 99.312 0.500
