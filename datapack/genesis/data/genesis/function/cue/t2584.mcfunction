setblock 48 66 69 minecraft:air
place feature minecraft:jungle_tree_no_vine 48 66 69
particle minecraft:happy_villager 48 69 69 1.5 2.5 1.5 0 30 force
particle minecraft:composter 48 67 69 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.738 98.093 0.500
