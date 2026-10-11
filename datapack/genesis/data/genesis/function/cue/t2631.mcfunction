setblock 103 69 14 minecraft:air
place feature minecraft:oak 103 69 14
particle minecraft:happy_villager 103 72 14 1.5 2.5 1.5 0 30 force
particle minecraft:composter 103 70 14 1 2 1 0 16 force
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
