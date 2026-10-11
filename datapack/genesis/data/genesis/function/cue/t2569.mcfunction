setblock 38 67 66 minecraft:air
place feature minecraft:jungle_bush 38 67 66
particle minecraft:happy_villager 38 70 66 1.5 2.5 1.5 0 30 force
particle minecraft:composter 38 68 66 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock 39 68 -61 minecraft:air
place feature minecraft:acacia 39 68 -61
particle minecraft:happy_villager 39 71 -61 1.5 2.5 1.5 0 30 force
particle minecraft:composter 39 69 -61 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -137.051 98.214 0.500
