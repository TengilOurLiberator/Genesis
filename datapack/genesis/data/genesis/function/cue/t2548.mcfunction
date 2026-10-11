setblock 26 67 81 minecraft:air
place feature minecraft:jungle_tree_no_vine 26 67 81
particle minecraft:happy_villager 26 70 81 1.5 2.5 1.5 0 30 force
particle minecraft:composter 26 68 81 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -137.691 98.463 0.500
