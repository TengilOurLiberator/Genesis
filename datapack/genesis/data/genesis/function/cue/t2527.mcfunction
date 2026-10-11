setblock 12 69 79 minecraft:air
place feature minecraft:jungle_tree_no_vine 12 69 79
particle minecraft:happy_villager 12 72 79 1.5 2.5 1.5 0 30 force
particle minecraft:composter 12 70 79 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -138.546 98.796 0.500
