setblock 84 69 39 minecraft:air
place feature minecraft:jungle_tree_no_vine 84 69 39
particle minecraft:happy_villager 84 72 39 1.5 2.5 1.5 0 30 force
particle minecraft:composter 84 70 39 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
