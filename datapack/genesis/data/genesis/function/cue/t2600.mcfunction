setblock 68 90 31 minecraft:air
place feature minecraft:spruce 68 90 31
particle minecraft:happy_villager 68 93 31 1.5 2.5 1.5 0 30 force
particle minecraft:composter 68 91 31 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
setblock 68 71 47 minecraft:air
place feature minecraft:jungle_tree_no_vine 68 71 47
particle minecraft:happy_villager 68 74 47 1.5 2.5 1.5 0 30 force
particle minecraft:composter 68 72 47 1 2 1 0 16 force
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -136.545 98.017 0.500
