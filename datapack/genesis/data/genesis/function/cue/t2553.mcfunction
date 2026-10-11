setblock 27 70 53 minecraft:air
place feature minecraft:jungle_tree_no_vine 27 70 53
particle minecraft:happy_villager 27 73 53 1.5 2.5 1.5 0 30 force
particle minecraft:composter 27 71 53 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -137.518 98.396 0.500
