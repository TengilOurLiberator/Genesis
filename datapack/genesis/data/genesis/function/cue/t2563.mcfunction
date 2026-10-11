setblock 34 66 78 minecraft:air
place feature minecraft:jungle_tree_no_vine 34 66 78
particle minecraft:happy_villager 34 69 78 1.5 2.5 1.5 0 30 force
particle minecraft:composter 34 67 78 1 2 1 0 16 force
setblock 35 91 -30 minecraft:air
place feature minecraft:spruce 35 91 -30
particle minecraft:happy_villager 35 94 -30 1.5 2.5 1.5 0 30 force
particle minecraft:composter 35 92 -30 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -137.211 98.276 0.500
