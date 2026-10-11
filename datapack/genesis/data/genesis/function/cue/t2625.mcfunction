setblock 94 79 -12 minecraft:air
place feature minecraft:spruce 94 79 -12
particle minecraft:happy_villager 94 82 -12 1.5 2.5 1.5 0 30 force
particle minecraft:composter 94 80 -12 1 2 1 0 16 force
setblock 94 71 28 minecraft:air
place feature minecraft:jungle_tree_no_vine 94 71 28
particle minecraft:happy_villager 94 74 28 1.5 2.5 1.5 0 30 force
particle minecraft:composter 94 72 28 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
