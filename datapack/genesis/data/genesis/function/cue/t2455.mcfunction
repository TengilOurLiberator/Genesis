setblock -34 68 84 minecraft:air
place feature minecraft:oak -34 68 84
particle minecraft:happy_villager -34 71 84 1.5 2.5 1.5 0 30 force
particle minecraft:composter -34 69 84 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -142.848 100.469 0.500
