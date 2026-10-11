setblock 59 68 53 minecraft:air
place feature minecraft:jungle_tree_no_vine 59 68 53
particle minecraft:happy_villager 59 71 53 1.5 2.5 1.5 0 30 force
particle minecraft:composter 59 69 53 1 2 1 0 16 force
setblock 59 70 -58 minecraft:air
place feature minecraft:acacia 59 70 -58
particle minecraft:happy_villager 59 73 -58 1.5 2.5 1.5 0 30 force
particle minecraft:composter 59 71 -58 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.599 98.039 0.500
