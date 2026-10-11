setblock 57 80 2 minecraft:air
place feature minecraft:oak 57 80 2
particle minecraft:happy_villager 57 83 2 1.5 2.5 1.5 0 30 force
particle minecraft:composter 57 81 2 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -106.509 84.003 0.500
